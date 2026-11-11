from PIL import Image, ImageDraw
import glob, os, sys
out = "folhas"  # pasta de saida das folhas (era a pasta temporaria da sessao)
os.makedirs(out,exist_ok=True)
def ruled(im, y0, y1):
    im=im.crop((0,y0,im.width,y1)).convert("RGB")
    R=Image.new("RGB",(im.width+28,im.height+14),(255,255,255)); R.paste(im,(28,14)); d=ImageDraw.Draw(R)
    for x in range(0,im.width,10):
        d.line([(28+x,0),(28+x,14 if x%50==0 else 6)],fill=(0,0,0))
        if x%50==0: d.text((30+x,0),str(x),fill=(200,0,0))
    for y in range(0,im.height,10):
        yy=y+y0
        d.line([(0 if yy%50==0 else 20,14+y),(28,14+y)],fill=(0,0,0))
        if yy%50==0: d.text((0,15+y),str(yy),fill=(200,0,0))
    # linhas guia finas a cada 50 sobre a imagem
    for x in range(50,im.width,50): d.line([(28+x,14),(28+x,R.height)],fill=(255,0,255))
    for y in range(0,im.height,50):
        if (y+y0)%50==0: d.line([(28,14+y),(R.width,14+y)],fill=(255,0,255))
    return R
def sheet(files, name, y0=0, y1=560):
    ims=[ruled(Image.open(f),y0,y1) for f in files]
    W=sum(i.width for i in ims)+8*len(ims); H=max(i.height for i in ims)
    s=Image.new("RGB",(W,H),(255,255,255)); x=0
    for i in ims: s.paste(i,(x,0)); x+=i.width+8
    s.save(os.path.join(out,name))
if __name__=="__main__":
    fs=sorted(glob.glob("*/000 inicial.png"))
    for k in range(0,len(fs),4):
        sheet(fs[k:k+4], f"r{k//4+1:02d}.png")
        print(k//4+1,[f.split(os.sep)[0][:28] for f in fs[k:k+4]])
