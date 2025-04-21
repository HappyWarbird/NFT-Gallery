import requests, mimetypes, datetime
from pathlib import Path
from config import ALCHEMY_API_KEY, ALCHEMY_CHAINS, WALLET_ADDRESS

baseDir = Path("data")
mainLog = Path("data/main.log")

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
                          "collectionName": t["contract"]["openSeaMetadata"]["collectionName"],
                          "contract": t["contract"]["address"],
                          "tokenID": t["tokenId"]})
        if data.get("pageKey") is not None:
            if data.get("pageKey") == pageKey:
                logHandler.write("[Error] Identical pageKey found for : " + walletAddress + " on " + chain + "\n")
                return None
            else:
                pageKey = data.get("pageKey")
                url = f"https://{chain}.g.alchemy.com/nft/v3/{apiKey}/getNFTsForOwner?owner={walletAddress}&withMetadata=true&pageKey={pageKey}&pageSize=100"
        else:
            pageKey = None
            hasNext = pageKey is not None
    return assetData

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

with open(mainLog, "a") as logHandler:
    logHandler.write("Starting Image Loader " + datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S") + "\n")
    for chain in ALCHEMY_CHAINS:
        assetData = getNftData(WALLET_ADDRESS, chain)
        for asset in assetData:
            if asset["imgURL"] is None:
                logHandler.write("Couldn't find image link for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                continue
            else:
                asset["imgData"] = imageLoader(asset["imgURL"])
                print("Processing data for " + asset["collectionName"] + " " + asset["tokenID"])
                if asset["imgData"]["fileExt"] in [".jpg", ".png"]:
                    logHandler.write("Processing image data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    #Handling of imagedata
                elif asset["imgData"]["fileExt"] in [".gif"]:
                    logHandler.write("Processing video data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    #Handling of videodata
                else:
                    logHandler.write("Couldn't handle image data for " + asset["contract"] + " " + asset["tokenID"] + "\n")
                    continue