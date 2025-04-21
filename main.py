import requests, mimetypes, datetime
from pathlib import Path
from config import ALCHEMY_API_KEY, ALCHEMY_CHAINS, WALLET_ADDRESS

baseDir = Path("data")
mainLog = Path("data/main.log")

def getNftData(walletAddress, chain):
    print("Getting NFTs for: " + walletAddress + " on " + chain)
    logHandler.write("Getting NFTs for: " + walletAddress + " on " + chain + "\n")
    apiKey = ALCHEMY_API_KEY
    url = f"https://{chain}.g.alchemy.com/nft/v3/{apiKey}/getNFTsForOwner?owner={walletAddress}&withMetadata=true&pageSize=100"
    links = []
    hasNext = True
    pageKey = None
    while hasNext:
        res = requests.get(url)
        data = res.json()

        for t in data.get("ownedNfts", {}):
            links.append({"image": t["image"]["originalUrl"],
                          "collectionName": t["contract"]["openSeaMetadata"]["collectionName"],
                          "contract": t["contract"]["address"],
                          "tokenID": t["tokenId"]})
        if data.get("pageKey") is not None:
            pageKey = data.get("pageKey")
            url = f"https://{chain}.g.alchemy.com/nft/v3/{apiKey}/getNFTsForOwner?owner={walletAddress}&withMetadata=true&pageKey={pageKey}&pageSize=100"
        else:
            pageKey = None
        hasNext = pageKey is not None

    return links
def imageLoader():
    for i in ALCHEMY_CHAINS:
        links = getNftData(WALLET_ADDRESS, i)
        for k in links:
            if k["image"] is None:
                logHandler.write("Couldn't find image link for " + k["contract"] + " " + k["tokenID"] + "\n")
                continue
            else:    
                try:
                    res = requests.get(k["image"])
                except:
                    logHandler.write("Couldn't download image for " + k["contract"] + " " + k["tokenID"] + "\n")
                    continue
                else:
                    if res.status_code != 200:
                        logHandler.write("Couldn't download image for " + k["contract"] + " " + k["tokenID"] + "\n")
                        continue
                    contentType = res.headers['content-type']
                    if contentType is None or "text/html":
                        logHandler.write("Couldn't match Content Type for " + k["contract"] + " " + k["tokenID"] + "\n")
                        continue
                    try:
                        with open(Path(baseDir / i / Path(k["contract"] + "-" + k["tokenID"] + mimetypes.guess_extension(contentType, strict=True))), "wb") as handler:
                            handler.write(res.content)
                    except:
                        logHandler.write("Couldn't save " + k["contract"] + " " + k["tokenID"] + "\n")
                        continue
                    else:
                        try:
                            print("Saved " + k["collectionName"] + " " + k["tokenID"])
                            logHandler.write("Saved " + k["contract"] + " " + k["tokenID"] + "\n")
                        except:
                            print("Saved " + k["contract"] + " " + k["tokenID"] + "\n")

with open(mainLog, "a") as logHandler:
    logHandler.write("Starting Image Loader " + datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S") + "\n")
    imageLoader()