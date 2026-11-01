from pathlib import Path
from PIL import Image, ImageDraw
import json, random, wave, struct, subprocess, shutil, zipfile

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build_v2'
RP=BUILD/'FixLagMCPE_BareBright_RP'
BP=BUILD/'FixLagMCPE_Lite_BP'
for p in (RP,BP):
    if p.exists(): shutil.rmtree(p)
    p.mkdir(parents=True)

RP_HEADER='a62d94f4-f6c6-48e3-9f3e-8f00f08d35a1'
RP_MODULE='4b4511b1-3cc1-44b2-a7f6-7d451a2911e2'
BP_HEADER='c07a1f4a-2f7d-43d5-a2f4-0a2dfb69e1a8'
BP_MODULE='271eb82f-4eb0-4a31-b850-740a5da0d831'

PALETTES={
 'stone':[(196,203,205,255),(220,226,224,255),(174,183,187,255),(234,237,231,255),(188,198,201,255)],
 'cobble':[(164,176,177,255),(197,207,204,255),(137,151,155,255),(219,224,217,255),(180,190,189,255)],
 'dirt':[(169,119,77,255),(188,143,94,255),(145,98,66,255),(202,157,105,255),(161,110,72,255)],
 'grass':[(105,181,72,255),(126,202,83,255),(86,163,63,255),(153,215,100,255),(112,191,75,255)],
 'sand':[(234,216,153,255),(249,233,178,255),(221,199,128,255),(255,241,194,255),(230,210,145,255)],
 'wood':[(174,124,75,255),(206,159,100,255),(148,101,62,255),(225,184,121,255),(190,139,83,255)],
 'leaves':[(71,151,70,255),(104,183,79,255),(54,128,61,255),(129,199,92,255),(89,168,73,255)],
 'ore_iron':[(170,183,184,255),(236,190,135,255),(212,217,209,255),(128,143,147,255)],
 'ore_gold':[(166,179,178,255),(255,215,91,255),(236,177,52,255),(203,210,201,255)],
 'ore_diamond':[(158,177,181,255),(87,224,213,255),(47,176,175,255),(214,240,231,255)],
 'ore_coal':[(172,183,181,255),(53,62,66,255),(33,42,47,255),(210,216,207,255)],
 'ore_emerald':[(165,181,173,255),(59,201,117,255),(32,151,92,255),(208,226,205,255)],
 'ore_lapis':[(163,181,190,255),(70,112,209,255),(43,78,164,255),(212,221,217,255)],
 'ore_redstone':[(166,177,178,255),(230,84,70,255),(177,51,49,255),(215,218,207,255)],
 'brick':[(178,115,91,255),(213,150,117,255),(147,88,75,255),(229,171,133,255)],
 'obsidian':[(57,50,85,255),(84,72,121,255),(39,37,65,255),(114,100,147,255)],
 'netherrack':[(128,69,62,255),(166,87,72,255),(96,49,48,255),(196,111,84,255)],
 'snow':[(235,245,247,255),(255,255,255,255),(211,231,239,255),(247,251,250,255)],
 'glass':[(171,220,235,110),(220,245,250,65),(255,255,255,150),(155,203,221,100)],
 'clay':[(173,190,190,255),(196,211,207,255),(151,173,176,255),(222,229,219,255)],
}

def texture(kind, seed=0, pattern='speckle'):
    rng=random.Random(seed); pal=PALETTES[kind]
    im=Image.new('RGBA',(16,16),pal[0]); px=im.load()
    if pattern=='brick':
        for y in range(16):
            row=y//4
            for x in range(16):
                xx=(x+(4 if row%2 else 0))%8
                px[x,y]=(235,220,190,255) if y%4==0 or xx==0 else pal[1+((x//3+y//4)%3)]
    elif pattern=='plank':
        for y in range(16):
            for x in range(16):
                px[x,y]=pal[2] if x in (0,7,15) else pal[(1+(y//5)+(1 if (x+y*3)%13==0 else 0))%len(pal)]
        for x,y in [(3,3),(11,11),(4,12)]:
            px[x,y]=pal[0]; px[x+1,y]=pal[2]
    elif pattern=='ore':
        for y in range(16):
            for x in range(16): px[x,y]=pal[0]
        for cx,cy in [(3,3),(10,4),(7,10),(13,13),(2,13)]:
            for dx,dy in [(0,0),(1,0),(0,1),(-1,0),(0,-1),(1,1)]:
                xx,yy=cx+dx,cy+dy
                if 0<=xx<16 and 0<=yy<16: px[xx,yy]=pal[1+((cx+cy)%min(3,len(pal)-1))]
        for _ in range(13):
            x,y=rng.randrange(16),rng.randrange(16); px[x,y]=pal[0]
    elif pattern=='cobble':
        for y in range(16):
            for x in range(16):
                row=y//4; col=(x+(3 if row%2 else 0))//5
                mortar=(y%4==0 or (x+(3 if row%2 else 0))%5==0)
                px[x,y]=(221,225,216,255) if mortar else pal[(col+row+rng.randrange(0,2))%len(pal)]
    elif pattern=='grass_side':
        for y in range(16):
            for x in range(16): px[x,y]=pal[(x+y)%len(pal)] if y<3 else PALETTES['dirt'][(x*2+y*3)%5]
        for x in range(16):
            if x%3: px[x,3]=(95,173,67,255)
    elif pattern=='grass_top':
        for y in range(16):
            for x in range(16): px[x,y]=pal[(x*3+y*5+(x*y)%7)%len(pal)]
        for _ in range(7):
            x,y=rng.randrange(16),rng.randrange(16); px[x,y]=(164,222,104,255)
    elif pattern=='glass':
        for y in range(16):
            for x in range(16): px[x,y]=(155,210,230,155) if x in (0,15) or y in (0,15) else (217,244,249,28)
        for x,y in [(2,2),(3,2),(12,13)]: px[x,y]=(255,255,255,220)
    else:
        for y in range(16):
            for x in range(16): px[x,y]=pal[(x*7+y*11+(x*y)%5+rng.randrange(2))%len(pal)]
        for _ in range(12):
            x,y=rng.randrange(16),rng.randrange(16); px[x,y]=pal[rng.randrange(len(pal))]
    return im

texdir=RP/'textures'/'blocks'; texdir.mkdir(parents=True)
ENV=RP/'textures'/'environment'; ENV.mkdir(parents=True)
texture_map={}
def save(name,kind,pattern='speckle',seed=0):
    texture(kind,seed,pattern).save(texdir/f'{name}.png',optimize=True)
    texture_map[name]=f'textures/blocks/{name}'

save('stone','stone',seed=1); save('stone_granite','stone',seed=3); save('stone_diorite','clay',seed=4); save('stone_andesite','stone',seed=8)
save('cobblestone','cobble','cobble',2); save('cobblestone_mossy','leaves',seed=5)
save('dirt','dirt',seed=4); save('coarse_dirt','dirt',seed=9); save('grass_top','grass','grass_top',2); save('grass_side','grass','grass_side',3)
save('sand','sand',seed=6); save('red_sand','brick',seed=7); save('gravel','cobble',seed=12)
save('sandstone_normal','sand','brick',2); save('sandstone_top','sand',seed=12); save('sandstone_bottom','sand',seed=13)
for name,seed in [('oak',1),('spruce',2),('birch',3),('jungle',4),('acacia',5),('big_oak',6)]:
    save(f'planks_{name}','wood','plank',seed)
save('log_oak','wood','plank',7); save('log_oak_top','wood','cobble',4); save('leaves_oak','leaves',seed=1)
save('glass','glass','glass',1)
for name,kind,seed in [('coal','ore_coal',1),('iron','ore_iron',2),('gold','ore_gold',3),('diamond','ore_diamond',4),('emerald','ore_emerald',5),('lapis','ore_lapis',6),('redstone','ore_redstone',7)]:
    save(f'{name}_ore',kind,'ore',seed)
save('obsidian','obsidian',seed=2); save('bedrock','stone','cobble',9); save('netherrack','netherrack',seed=3); save('bricks','brick','brick',1)
save('stonebrick','stone','brick',2); save('snow','snow',seed=3); save('clay','clay',seed=4)
save('glowstone','sand',seed=10); save('moss_block','leaves',seed=10); save('deepslate','obsidian',seed=12)

aliases={'stone_granite_smooth':'stone_granite','stone_diorite_smooth':'stone_diorite','stone_andesite_smooth':'stone_andesite',
 'grass_carried':'grass_side','grass_carried_top':'grass_top','grass_bottom':'dirt','dirt_podzol_top':'dirt','dirt_podzol_bottom':'dirt',
 'cobblestone_wall':'cobblestone','planks':'planks_oak','leaves':'leaves_oak','glass_pane_top':'glass'}
texture_data={k:{'textures':v} for k,v in texture_map.items()}
for alias,target in aliases.items(): texture_data[alias]={'textures':texture_map[target]}
(RP/'textures'/'terrain_texture.json').write_text(json.dumps({'resource_pack_name':'FixLagMCPE_BareBright','texture_name':'atlas.terrain','padding':2,'num_mip_levels':1,'texture_data':texture_data},indent=2),encoding='utf-8')
(RP/'textures'/'flipbook_textures.json').write_text('[]\n',encoding='utf-8')

cloud=Image.new('RGBA',(64,64),(255,255,255,0)); d=ImageDraw.Draw(cloud)
for ox,oy in [(0,5),(22,5),(44,5),(0,37),(22,37),(44,37)]:
    d.rectangle((ox,oy+5,ox+17,oy+14),fill=(255,255,255,255))
    d.rectangle((ox+4,oy+1,ox+13,oy+13),fill=(255,255,255,255))
    d.rectangle((ox+17,oy+8,ox+21,oy+13),fill=(255,255,255,255))
    d.rectangle((ox+2,oy+14,ox+19,oy+15),fill=(255,255,255,255))
cloud.save(ENV/'clouds.png',optimize=True)

fog={'format_version':'1.16.100','minecraft:fog_settings':{
 'description':{'identifier':'fixlagmcpe:clear_medium'},
 'distance':{
  'air':{'fog_start':0.0,'fog_end':1000.0,'fog_color':'#DDF4FF','render_distance_type':'fixed'},
  'weather':{'fog_start':0.0,'fog_end':1000.0,'fog_color':'#DDF4FF','render_distance_type':'fixed'},
  'water':{'fog_start':0.0,'fog_end':1000.0,'fog_color':'#A8DFFF','render_distance_type':'fixed','transition_fog':{'init_fog':{'fog_start':0.0,'fog_end':0.01,'fog_color':'#A8DFFF','render_distance_type':'fixed'},'min_percent':0.25,'mid_seconds':1,'mid_percent':0.6,'max_seconds':2}},
  'lava':{'fog_start':0.0,'fog_end':256.0,'fog_color':'#F7A16B','render_distance_type':'fixed'},
  'lava_resistance':{'fog_start':0.0,'fog_end':1000.0,'fog_color':'#F7A16B','render_distance_type':'fixed'}},
 'volumetric':{'density':{'water':{'max_density':0.0,'uniform':True},'lava':{'max_density':0.03,'uniform':True},'lava_resistance':{'max_density':0.0,'uniform':True}}}}}
(RP/'fogs').mkdir(); (RP/'fogs'/'clear_medium.json').write_text(json.dumps(fog,indent=2),encoding='utf-8')

sounddir=RP/'sounds'/'fixlagmcpe'; sounddir.mkdir(parents=True)
import numpy as np
SR=22050
def synth(kind,seed):
    rng=np.random.default_rng(seed)
    if kind in ('stone_dig','stone_place'):
        dur=.19 if kind=='stone_dig' else .13; n=int(SR*dur); t=np.arange(n)/SR
        noise=rng.normal(0,1,n); env=np.exp(-t*(18 if kind=='stone_dig' else 28))
        tone=np.sin(2*np.pi*(190 if kind=='stone_dig' else 310)*t)*np.exp(-t*22)
        x=.52*noise*env+.35*tone
        x[:180]+=rng.normal(0,.7,min(180,n))*np.linspace(1,.05,min(180,n))
    elif kind in ('dirt_dig','dirt_place'):
        dur=.17 if kind=='dirt_dig' else .11; n=int(SR*dur); t=np.arange(n)/SR
        x=.6*rng.normal(0,1,n)*np.exp(-t*23)+.24*np.sin(2*np.pi*(120 if kind=='dirt_dig' else 175)*t)*np.exp(-t*25)
    else:
        dur=.2 if kind=='wood_dig' else .14; n=int(SR*dur); t=np.arange(n)/SR
        f=420 if kind=='wood_dig' else 520
        x=.24*rng.normal(0,1,n)*np.exp(-t*25)+.5*np.sin(2*np.pi*f*t)*np.exp(-t*16)
        x+=.18*np.sin(2*np.pi*(f*1.48)*t)*np.exp(-np.maximum(0,t-.035)*35)*(t>.035)
    fade=min(int(SR*.012),len(x)//4)
    x[:fade]*=np.linspace(0,1,fade); x[-fade:]*=np.linspace(1,0,fade)
    x=np.clip(x/max(1e-8,np.max(np.abs(x)))*.68,-1,1)
    return (x*32767).astype('<i2')

sound_names=['stone_dig','stone_place','dirt_dig','dirt_place','wood_dig','wood_place']
for i,name in enumerate(sound_names):
    samples=synth(name,230+i); wavfile=sounddir/(name+'.wav')
    with wave.open(str(wavfile),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(samples.tobytes())
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(wavfile),'-c:a','libvorbis','-q:a','3',str(sounddir/(name+'.ogg'))],check=True)
    wavfile.unlink()

sound_definitions={'format_version':'1.14.0','sound_definitions':{}}
for name in sound_names: sound_definitions['sound_definitions'][f'fixlagmcpe.{name}']={'category':'block','sounds':[{'name':f'sounds/fixlagmcpe/{name}','volume':0.9,'pitch':1.0}]}
(RP/'sounds').mkdir(exist_ok=True)
(RP/'sounds'/'sound_definitions.json').write_text(json.dumps(sound_definitions,indent=2),encoding='utf-8')
groups={}
for group,dig,place in [('stone','stone_dig','stone_place'),('normal','stone_dig','stone_place'),('gravel','dirt_dig','dirt_place'),('sand','dirt_dig','dirt_place'),('grass','dirt_dig','dirt_place'),('wood','wood_dig','wood_place'),('metal','stone_dig','stone_place'),('netherrack','stone_dig','stone_place')]:
    groups[group]={'events':{'break':{'sound':f'fixlagmcpe.{dig}','volume':.9,'pitch':[.94,1.06]},'place':{'sound':f'fixlagmcpe.{place}','volume':.86,'pitch':[.94,1.06]}},'pitch':1.0,'volume':1.0}
(RP/'sounds.json').write_text(json.dumps({'block_sounds':groups},indent=2),encoding='utf-8')

rp_manifest={'format_version':2,'header':{'name':'FixLagMCPE | BareBright Lite','description':'Texture sáng 16x16 có hoa văn nhỏ, mây pixel, âm thanh mới và fog nước/lava giảm.','uuid':RP_HEADER,'version':[2,0,0],'min_engine_version':[1,21,0]},'modules':[{'type':'resources','uuid':RP_MODULE,'version':[2,0,0]}]}
(RP/'manifest.json').write_text(json.dumps(rp_manifest,indent=2),encoding='utf-8')
icon=Image.new('RGBA',(64,64),(135,201,230,255)); dr=ImageDraw.Draw(icon)
dr.rectangle((0,38,63,63),fill=(124,190,93,255)); dr.rectangle((0,46,63,63),fill=(173,129,84,255))
dr.rectangle((9,28,24,34),fill=(255,255,255,255)); dr.rectangle((13,23,21,33),fill=(255,255,255,255))
dr.rectangle((37,18,55,25),fill=(255,255,255,255)); dr.rectangle((42,13,51,24),fill=(255,255,255,255))
icon.save(RP/'pack_icon.png')

(BP/'functions').mkdir(parents=True)
(BP/'functions'/'tick.json').write_text(json.dumps({'values':['tick']},indent=2),encoding='utf-8')
(BP/'functions'/'tick.mcfunction').write_text('execute as @a[tag=!flmcpe_fog] run fog @s push fixlagmcpe:clear_medium flmcpe_clear\nexecute as @a[tag=!flmcpe_fog] run tag @s add flmcpe_fog\n',encoding='utf-8')
(BP/'functions'/'remove_fog.mcfunction').write_text('fog @s remove flmcpe_clear\ntag @s remove flmcpe_fog\n',encoding='utf-8')
(BP/'functions'/'apply_fog.mcfunction').write_text('fog @s push fixlagmcpe:clear_medium flmcpe_clear\ntag @s add flmcpe_fog\n',encoding='utf-8')
(BP/'README.txt').write_text('Requires the matching FixLagMCPE resource pack.\nThe tick function applies custom fog once per player; /function remove_fog resets it and /function apply_fog reapplies it.\n',encoding='utf-8')
bp_manifest={'format_version':2,'header':{'name':'FixLagMCPE | Lite Behavior','description':'Giảm fog nước/lava bằng fog custom.','uuid':BP_HEADER,'version':[2,0,0],'min_engine_version':[1,21,0]},'modules':[{'type':'data','uuid':BP_MODULE,'version':[2,0,0]}],'dependencies':[{'uuid':RP_HEADER,'version':[2,0,0]}]}
(BP/'manifest.json').write_text(json.dumps(bp_manifest,indent=2),encoding='utf-8')
bicon=Image.new('RGBA',(64,64),(65,111,138,255)); bd=ImageDraw.Draw(bicon)
bd.rectangle((10,10,54,54),outline=(244,247,226,255),width=4); bd.line((18,32,28,42,47,21),fill=(160,229,129,255),width=6); bicon.save(BP/'pack_icon.png')

OUT=ROOT/'dist'; OUT.mkdir(exist_ok=True)
def pack(folder,dest):
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for f in sorted(folder.rglob('*')):
            if f.is_file(): z.write(f,f.relative_to(folder).as_posix())
    with zipfile.ZipFile(dest) as z:
        if z.testzip(): raise RuntimeError(f'Corrupt archive: {dest}')

rp_file=OUT/'FixLagMCPE_BareBright_Lite.mcpack'
bp_file=OUT/'FixLagMCPE_Lite_Behavior.mcpack'
addon=OUT/'FixLagMCPE_BareBright_v2.mcaddon'
pack(RP,rp_file); pack(BP,bp_file)
with zipfile.ZipFile(addon,'w',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
    z.write(rp_file,rp_file.name); z.write(bp_file,bp_file.name)
with zipfile.ZipFile(addon) as z:
    if z.testzip(): raise RuntimeError('Corrupt mcaddon')

names=['stone','cobblestone','dirt','grass_top','sand','planks_oak','leaves_oak','iron_ore','diamond_ore','bricks','obsidian','netherrack']
preview=Image.new('RGB',(600,300),(240,244,238)); pd=ImageDraw.Draw(preview)
for i,name in enumerate(names):
    x=(i%6)*100; y=(i//6)*150
    im=Image.open(texdir/f'{name}.png').convert('RGBA').resize((80,80),Image.Resampling.NEAREST)
    preview.paste(im,(x+10,y+8),im); pd.text((x+8,y+95),name,fill=(20,30,35))
preview.save(OUT/'FixLagMCPE_texture_preview.png')
for folder in (RP,BP):
    for f in folder.rglob('*.json'): json.loads(f.read_text(encoding='utf-8'))
assert json.loads((RP/'textures'/'flipbook_textures.json').read_text())==[]
print(json.dumps({'resource_pack':str(rp_file),'behavior_pack':str(bp_file),'addon':str(addon),'textures':len(texture_data),'sounds':len(sound_names),'rp_files':sum(p.is_file() for p in RP.rglob('*')),'bp_files':sum(p.is_file() for p in BP.rglob('*')),'addon_bytes':addon.stat().st_size},indent=2))
