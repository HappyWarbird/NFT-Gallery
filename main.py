import requests, mimetypes, datetime, io
from PIL import Image
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
            assetData.append({"imgURL": t["image"]["originalUrl"],
                          "collectionName": t["collection"]["name"],
                          "contract": t["contract"]["address"],
                          "tokenID": t["tokenId"],
                          "isSpam": t["contract"]["isSpam"],
                          "metadata": t["raw"]["metadata"]})
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
def imageResizer(imageData):
    image = Image.open(io.BytesIO(imageData))
    if image.width == image.height:
        image.resize((1080, 1080))
        return image
    else:
        width, height = image.size
        if width > height:
            image.resize((1080, round(1080/width*height)))
            return image
        else:
            image.resize((round(1080/height*width), 1080))
            return image
        
### Creating Collection Info
def getCollInfo(asset):
    image = Image.open()
    return image

with open(mainLog, "a") as logHandler:
    #Log Handling
    logHandler.write("Starting Image Loader " + datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S") + "\n")
    for chain in ALCHEMY_CHAINS:
        assetData = getNftData(WALLET_ADDRESS, chain)
        for asset in assetData:
            #Creating Collection Folder
            (BASE_DIR / chain / asset["contract"]).mkdir(parents=True, exist_ok=True)
            if asset["imgURL"] is None:
                logHandler.write("Couldn't find image link for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                continue
            elif asset["isSpam"] is True:
                logHandler.write("Collection marked as Spam: " + asset["contract"] + " " + asset["tokenID"] + "\n")
                continue
            else:
                asset["imgData"] = imageLoader(asset["imgURL"])
                print("Processing data for " + asset["collectionName"] + " " + asset["tokenID"])
                if asset["imgData"]["fileExt"] in [".jpg", ".png"]:
                    #Handling of imagedata
                    logHandler.write("Resizing image data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    imgAsset = imageResizer(asset["imgData"]["binary"])
                    logHandler.write("Creating collection info for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    imgInfo = getCollInfo(asset)
                elif asset["imgData"]["fileExt"] in [".gif"]:
                    #Handling of videodata
                    logHandler.write("Processing video data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    
                else:
                    #Can't handle that stuff or it is None...
                    logHandler.write("Couldn't handle image data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    continue