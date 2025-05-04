import requests, mimetypes, datetime, io
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from config import ALCHEMY_API_KEY, ALCHEMY_CHAINS, WALLET_ADDRESS, BASE_DIR

mainLog = Path("data/main.log")

### Getting owned NFT Metadata from Alchemy NFT-API
def getNftData(walletAddress, chain):
    print("Getting NFT Data for: " + walletAddress + " on " + chain)
    logHandler.write("Getting NFTs for: " + walletAddress + " on " + chain + "\n")
    apiKey = ALCHEMY_API_KEY
    url = f"https://{chain}.g.alchemy.com/nft/v3/{apiKey}/getNFTsForOwner?owner={walletAddress}&withMetadata=true&pageSize=100"
    assetData = []
    hasNext = True
    pageKey = None
    while hasNext:
        res = requests.get(url)
        data = res.json()

        for t in data.get("ownedNfts", {}):
            assetData.append({"imgUrl": t["image"]["cachedUrl"],
                              "imgType": t["image"]["contentType"],
                              "pngUrl": t["image"]["pngUrl"],
                              "origUrl": t["image"]["originalUrl"],
                              "collectionName": t["contract"]["name"],
                              "contract": t["contract"]["address"],
                              "tokenID": t["tokenId"],
                              "isSpam": t["contract"]["isSpam"]})
        #Pagination Handling, preventing identical pageKey Bug
        if data.get("pageKey") is not None:
            if data.get("pageKey") == pageKey:
                logHandler.write("[Error] Identical pageKey found for : " + walletAddress + " on " + chain + "\n")
                exit()
            else:
                pageKey = data.get("pageKey")
                url = f"https://{chain}.g.alchemy.com/nft/v3/{apiKey}/getNFTsForOwner?owner={walletAddress}&withMetadata=true&pageKey={pageKey}&pageSize=100"
        else:
            pageKey = None
            hasNext = pageKey is not None
    return assetData

### Getting binary Image/Video Data and Filetype
def imageLoader(imgURL):
    logHandler.write("Getting Image Data from: " + imgURL + "\n")
    imgData = {}
    try:
        res = requests.get(imgURL)
    except:
        logHandler.write("[Error] on requesting " + imgURL + "\n")
        return None
    else:
        if res.status_code != 200:
            logHandler.write("[Error] Response is not 200 from " + imgURL + "\n")
            return None
        else:
            contentType = res.headers['content-type']
            if contentType is None:
                logHandler.write("[Error] Could not match Content Type from " + imgURL + "\n")
                return None
            else:
                imgData["binary"] = res.content
                imgData["fileExt"] = mimetypes.guess_extension(contentType, strict=True)
                return imgData

### Resizing image to maxsize relative 1080x1080
def imageResizer(image):
    if image.width == image.height:
        img = image.resize((1080, 1080))
        return img
    else:
        width, height = image.size
        if width > height:
            img = Image.new("RGBA", (1080, 1080))
            imgres = image.resize((1080, round(1080/width*height)))
            img.paste(imgres, (0, round((1080-(1080/width*height))/2)))
            return img
        else:
            img = Image.new("RGBA", (1080, 1080))
            imgres = image.resize((round(1080/height*width), 1080))
            img.paste(imgres, (round((1080-(1080/height*width))/2), 0))
            return img
        
### Creating Collection Info
def getInfoPanel(asset):
    bg = Image.open("collInfoBG.png")
    img = ImageDraw.Draw(bg)
    collFont = ImageFont.truetype("Girassol-Regular.ttf", 60)
    if asset["collectionName"] is None:
        img.text((50, 30), str(asset["contract"]), font=collFont, fill=(0, 0, 0))
    else:
        img.text((50, 30), str(asset["collectionName"]), font=collFont, fill=(0, 0, 0))
    img.text((50, 100), "#" + str(asset["tokenID"]), font=collFont, fill=(0, 0, 0))
    return bg

def createImage(imageData, collInfo):
    original = Image.open(io.BytesIO(imageData))
    new = Image.new("RGBA", (1080, 1300))
    original = imageResizer(original)
    new.paste(original.convert("RGBA"), (0, 0))
    new.paste(collInfo, (0, 1081))
    return new

def createGif(gifData, collInfo):
    original = Image.open(io.BytesIO(gifData))
    gifFrames = []
    for frame in range(original.n_frames):
        original.seek(frame)
        new = Image.new("RGBA", (1080, 1300))
        origFrame = imageResizer(original)
        new.paste(origFrame.convert("RGBA"), (0, 0))
        new.paste(collInfo, (0, 1081))
        gifFrames.append(new)
    return gifFrames

with open(mainLog, "a") as logHandler:
    #Log Handling
    logHandler.write("Starting Image Loader " + datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S") + "\n")
    for chain in ALCHEMY_CHAINS:
        assetData = getNftData(WALLET_ADDRESS, chain)
        for asset in assetData:
            if asset["isSpam"] is True:
                logHandler.write("Collection marked as Spam: " + asset["contract"] + " " + asset["tokenID"] + "\n")
                continue
            elif asset["imgUrl"] is None:
                asset["imgUrl"] = asset["origUrl"]
            else:
                if asset["imgType"] == "image/svg+xml":
                    asset["imgData"] = imageLoader(asset["pngUrl"])
                else:
                    asset["imgData"] = imageLoader(asset["imgUrl"])
                if asset["imgData"] is None:
                    logHandler.write("No Image Data found for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    continue
                #Creating Collection Folder
                (Path(BASE_DIR) / chain).mkdir(parents=True, exist_ok=True)
                print("Processing data for " + str(asset["collectionName"]) + " " + asset["tokenID"])
                if asset["imgData"]["fileExt"] in [".jpg", ".png"]:
                    #Handling of imagedata
                    logHandler.write("Processing image data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    imgInfo = getInfoPanel(asset)
                    img = createImage(asset["imgData"]["binary"], imgInfo)
                    img.save(Path(BASE_DIR) / chain / (asset["contract"] + "-" + asset["tokenID"] + ".png"))
                    logHandler.write("Saved image data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                elif asset["imgData"]["fileExt"] in [".gif"]:
                    #Handling of gifdata
                    logHandler.write("Processing gif data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    gifInfo = getInfoPanel(asset)
                    gifFrames = createGif(asset["imgData"]["binary"], gifInfo)
                    gifFrames[0].save(Path(BASE_DIR) / chain / (asset["contract"] + "-" + asset["tokenID"] + ".gif"), save_all=True, append_images=gifFrames[1:], loop=1)
                    logHandler.write("Saved gif data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                elif asset["imgData"]["fileExt"] in [".mp4", ".webm"]:
                    #Handling of videodata
                    logHandler.write("Processing video data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    
                else:
                    #Can't handle that stuff or it is None...
                    logHandler.write("Couldn't handle image data for " + asset["contract"] + " " + asset["tokenID"] + "\n")