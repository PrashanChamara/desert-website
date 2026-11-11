"""Deterministic 2D deformation study. Not a 3D reconstruction or skeletal rig."""
from PIL import Image
import numpy as np
from scipy.ndimage import map_coordinates
from pathlib import Path
import subprocess, json
ROOT=Path(__file__).parent
SRC=ROOT/'sources'; OUT=ROOT/'assets'; OUT.mkdir(exist_ok=True)
W,H=512,640; FPS=24
Y,X=np.mgrid[0:H,0:W].astype(np.float32)
x=X/W;y=Y/H

def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)

def source(name):
 im=Image.open(SRC/name).convert('RGBA'); im.thumbnail((480,600),Image.Resampling.LANCZOS)
 base=Image.new('RGBA',(W,H));base.alpha_composite(im,((W-im.width)//2,620-im.height))
 return np.array(base)

def frame(a,state,t,duration):
 p=2*np.pi*t/duration
 dx=np.zeros_like(X);dy=np.zeros_like(Y)
 if state!='pause_idle':
  upper=1-smooth(.70,.97,y)
  dy+=1.7*np.sin(p)*upper
  dx+=.65*np.sin(p)*upper
  # Flag fabric displacement fades out at pole and preserves the crest at small amplitude.
  if state=='greeting_wave':
   flag=smooth(.63,.83,x)*(1-smooth(.34,.47,y))
  else:
   flag=(1-smooth(.33,.43,x))*(1-smooth(.32,.46,y))
  amp=3.5 if state=='flag_wave_loop' else 1.3
  dy+=amp*flag*np.sin(p*2+x*13)
  dx+=amp*.35*flag*np.sin(p*2+x*11)
 if state=='greeting_wave':
  # Localized paw/forearm deformation, anchored at the shoulder.
  arm=(1-smooth(.22,.35,x))*smooth(.19,.29,y)*(1-smooth(.43,.52,y))
  dx+=9*np.sin(p*3)*arm
  dy+=3*np.sin(p*3+.3)*arm
 if state=='walk_loop':
  # Limited 2D stepping study; no claim of physically correct foot contacts.
  lower=smooth(.62,.91,y)
  side=np.tanh((x-.60)*22)
  dx+=9*np.sin(p)*side*lower
  dy+=-5*np.sin(p)*side*lower
  dy+=2*np.cos(p*2)*(1-smooth(.84,.98,y))
 coords=np.array([Y-dy,X-dx])
 # Premultiplied resampling prevents dark fringes on alpha boundaries.
 alpha=a[:,:,3].astype(np.float32)/255
 chans=[map_coordinates(a[:,:,c].astype(np.float32)*alpha,coords,order=1,mode='constant',cval=0) for c in range(3)]
 aa=map_coordinates(alpha,coords,order=1,mode='constant',cval=0)
 rgb=np.stack(chans,axis=2)/np.maximum(aa[:,:,None],1e-6)
 return np.dstack([np.clip(rgb,0,255),np.clip(aa*255,0,255)]).astype(np.uint8)

states={'idle_loop':('mascot-idle-01.png',4),'walk_loop':('mascot-walk-01.png',1.25),'greeting_wave':('mascot-wave-01.png',3),'flag_wave_loop':('mascot-idle-01.png',3),'pause_idle':('mascot-idle-01.png',1)}
manifest={'format':'VP9 WebM with alpha','dimensions':[W,H],'fps':FPS,'status':'2D motion prototype; not production-approved; not a 3D model','states':{}}
for state,(name,duration) in states.items():
 a=source(name)
 cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','31','-deadline','good','-cpu-used','4','-auto-alt-ref','0',str(OUT/(state+'.webm'))]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 n=round(duration*FPS)
 for i in range(n):proc.stdin.write(frame(a,state,i/FPS,duration).tobytes())
 proc.stdin.close()
 if proc.wait():raise RuntimeError(state)
 Image.fromarray(frame(a,state,0,duration)).save(OUT/(state+'.png'))
 manifest['states'][state]={'file':state+'.webm','duration':n/FPS,'loop':state!='greeting_wave','bytes':(OUT/(state+'.webm')).stat().st_size}
 print(state,manifest['states'][state],flush=True)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
