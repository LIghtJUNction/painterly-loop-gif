#!/usr/bin/env python3
"""Animate an opaque painted scene with streamed FFmpeg processing.

Python writes expressions / metadata only. FFmpeg performs every image and
video operation. The protected upper scene stays geometrically fixed;
periodic deformation is limited to the lower foreground. A scrolling
rain layer and analytic golden fireflies repeat after an integer frame cycle.
"""
from pathlib import Path
import argparse, hashlib, json, math, random, shutil, subprocess

def run(*args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-8000:])
    return p.stdout

def ffmpeg(*args):
    return run('ffmpeg','-hide_banner','-loglevel','error','-y','-threads','1',
               '-filter_threads','1','-filter_complex_threads','1',*args)

def probe(path):
    return json.loads(run('ffprobe','-v','error','-count_frames','-show_entries',
      'format=duration,size:stream=width,height,nb_frames,nb_read_frames,codec_name,pix_fmt,avg_frame_rate',
      '-of','json',str(path)))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sample=Path(__file__).resolve().parent.parent/'assets/examples/night-garden-background.png'
    p.add_argument('--background',type=Path,default=sample,help='Original still image; defaults to the bundled example.')
    p.add_argument('--output',type=Path,default=Path('painterly-loop.gif'),help='GIF destination; MP4 and proof use the same stem.')
    p.add_argument('--width',type=int,default=384);p.add_argument('--fps',type=int,default=24)
    p.add_argument('--duration',type=float,default=4.8);p.add_argument('--seed',type=int,default=37)
    p.add_argument('--rain-streaks',type=int,default=62,help='Number of rain streaks; 0 disables rain.')
    p.add_argument('--fireflies',type=int,default=27,help='Number of warm drifting light points; 0 disables them.')
    p.add_argument('--sway-px',type=float,default=3.2,help='Foreground horizontal displacement strength in output pixels.')
    p.add_argument('--protect-top',type=float,default=.54,help='Fraction of height kept geometrically fixed, 0–1.')
    p.add_argument('--overwrite',action='store_true',help='Replace this output name and its derived artifacts.')
    a=p.parse_args();bg=a.background.resolve();out=a.output.resolve()
    if not bg.is_file():p.error(f'Background not found: {bg}')
    if out.suffix.lower()!='.gif':p.error('Output must end in .gif.')
    if bg==out or bg==out.with_suffix('.mp4'):p.error('Output must not replace the input background.')
    if a.width<=0 or a.width%2:p.error('Width must be positive and even for the yuv420p MP4.')
    if not 1<=a.fps<=100:p.error('FPS must be 1–100; GIF delays have 10 ms resolution.')
    if not math.isfinite(a.duration) or a.duration<=0 or round(a.duration*a.fps)<2:p.error('Duration must be finite and contain at least two frames.')
    if a.rain_streaks<0 or a.fireflies<0:p.error('Particle counts must be nonnegative.')
    if not math.isfinite(a.sway_px) or a.sway_px<0:p.error('Sway must be finite and nonnegative.')
    if not math.isfinite(a.protect_top) or not 0<=a.protect_top<=1:p.error('Protect-top must be between 0 and 1.')
    if not a.overwrite and (out.exists() or out.with_suffix('.mp4').exists()):p.error('Output already exists; choose a new name or use --overwrite.')
    for tool in ('ffmpeg','ffprobe'):
        if not shutil.which(tool):p.error(f'{tool} is required on PATH.')
    dims=probe(bg)['streams'][0];w=a.width;h=max(2,round(dims['height']/dims['width']*w/2)*2)
    out.parent.mkdir(parents=True,exist_ok=True);work=out.parent/(out.stem+'-render');work.mkdir(exist_ok=True)
    count=round(a.duration*a.fps);period=count/a.fps
    rng=random.Random(a.seed)
    # Protect geometry in the upper region; overlay particles may pass over it.
    # The side-weight also reduces deformation across the central stone path.
    weight=f'pow(max(0,(Y/H-{a.protect_top:.12f})/{1-a.protect_top:.12f}),1.35)*min(1,abs(X/W-0.5)/0.20)' if a.protect_top<1 else '0'
    xe=f'128+({weight})*({a.sway_px:.12f}*sin(2*PI*T/{period:.12f}+Y/41)+{a.sway_px*1.1/3.2:.12f}*sin(4*PI*T/{period:.12f}+X/69))'
    ye=f'128+({weight})*{a.sway_px*1.3/3.2:.12f}*sin(2*PI*T/{period:.12f}+X/57+1.2)'
    graph=[f'[0:v]scale={w}:{h}:flags=lanczos,format=gbrp,setpts=PTS-STARTPTS[base]',
      f"nullsrc=s={w}x{h}:r={a.fps}:d={period:.12f},format=gbrp,geq=r='{xe}':g='{xe}':b='{xe}'[xmap]",
      f"nullsrc=s={w}x{h}:r={a.fps}:d={period:.12f},format=gbrp,geq=r='{ye}':g='{ye}':b='{ye}'[ymap]",
      '[base][xmap][ymap]displace=edge=smear[garden]']
    rain=f'color=c=black:s={w}x{h}:r={a.fps}:d={period:.12f},format=gbrp'
    rain_specs=[]
    for n in range(a.rain_streaks):
        x=rng.randrange(w);y=rng.randrange(h);length=rng.randrange(5,17)
        grey=rng.randrange(100,183)
        rain+=f',drawbox=x={x}:y={y}:w=1:h={length}:color=0x{grey:02x}{grey:02x}{grey:02x}:t=fill'
        rain_specs.append([x,y,length,grey])
    # FFmpeg scroll samples at a positive offset; negative speed moves the
    # visible streaks downward, as verified with a two-frame bright marker.
    rain+=f',scroll=vertical={-1/count:.12f}[rain]';graph.append(rain)
    sw=64;sh=max(1,round(h/w*sw));lights=[];terms=[]
    for n in range(a.fireflies):
        x=rng.uniform(5,sw-5);y=rng.uniform(4,sh*.72)
        # Leave the warm greenhouse readable without large crossing glows.
        if .17*sw<x<.38*sw and .24*sh<y<.47*sh:y=sh*.18
        phase=rng.uniform(0,2*math.pi);dx=rng.uniform(.5,1.5);dy=rng.uniform(.5,1.4)
        radius=rng.uniform(.30,.55);cycles=rng.choice([1,2,3])
        xx=f'({x:.5f}+{dx:.5f}*cos(2*PI*T/{period:.12f}+{phase:.5f}))'
        yy=f'({y:.5f}+{dy:.5f}*sin(2*PI*T/{period:.12f}+{phase:.5f}))'
        dist=f'((X-{xx})*(X-{xx})+(Y-{yy})*(Y-{yy}))'
        pulse=f'(.20+.80*pow(.5+.5*sin({cycles}*2*PI*T/{period:.12f}+{phase:.5f}),2))'
        terms.append(f'{pulse}*(.88*exp(-{dist}/{radius*radius:.5f})+.16*exp(-{dist}/{(radius*2.6)**2:.5f}))')
        lights.append({'x':x,'y':y,'dx':dx,'dy':dy,'radius':radius,'phase':phase,'blink_cycles':cycles})
    field='+'.join(terms) or '0'
    graph.append(f"nullsrc=s={sw}x{sh}:r={a.fps}:d={period:.12f},format=gbrp,geq=r='255*({field})':g='195*({field})':b='70*({field})',scale={w}:{h}:flags=bicubic[flies]")
    graph.extend(['[garden][rain]blend=all_mode=screen:all_opacity=.18[rained]',
      '[rained][flies]blend=all_mode=screen:all_opacity=.92,format=rgb24[out]'])
    graph_path=work/'filters.txt';graph_path.write_text(';\n'.join(graph),encoding='utf-8')
    clip=work/'motion.mkv'
    ffmpeg('-loop','1','-framerate',str(a.fps),'-i',str(bg),'-filter_complex',graph_path.read_text(),
      '-map','[out]','-frames:v',str(count),'-c:v','ffv1','-level','3','-pix_fmt','bgr0',str(clip))
    palette=work/'palette.png'
    ffmpeg('-i',str(clip),'-vf','palettegen=max_colors=256:stats_mode=diff','-frames:v','1',str(palette))
    ffmpeg('-i',str(clip),'-i',str(palette),'-lavfi','paletteuse=dither=sierra2_4a:diff_mode=rectangle',
      '-loop','0',str(out))
    ffmpeg('-i',str(clip),'-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p',
      '-movflags','+faststart',str(out.with_suffix('.mp4')))
    actual=probe(out);s=actual['streams'][0];frames=int(s.get('nb_read_frames',s.get('nb_frames',0)))
    indexes=sorted(set(round(i*(frames-1)/5) for i in range(6)))
    select='+'.join(f'eq(n\\,{n})' for n in indexes)
    ffmpeg('-i',str(out),'-vf',f'select={select},scale=240:-1:flags=lanczos,tile=3x2:padding=8:margin=8:color=0x070d18',
      '-frames:v','1',str(out.with_name(out.stem+'-decoded-contact.jpg')))
    for label,n in [('first',0),('middle',frames//2),('last',frames-1)]:
        ffmpeg('-i',str(out),'-vf',f'select=eq(n\\,{n})','-frames:v','1',str(out.with_name(out.stem+f'-decoded-{label}.png')))
    ffmpeg('-i',str(out.with_name(out.stem+'-decoded-first.png')),'-vf','scale=240:-1:flags=lanczos',
      '-frames:v','1',str(out.with_name(out.stem+'-mobile.png')))
    # Decode to small grayscale frames solely for numeric motion/seam evidence.
    # No Python creates or edits images and only one64×72 frame is held at once.
    tiny_h=max(1,round(h/w*64))
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-threads','1','-filter_threads','1','-i',str(out),
      '-vf',f'scale=64:{tiny_h}:flags=area,format=gray','-threads','1','-f','rawvideo','pipe:1']
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    length=64*tiny_h;first=None;previous=None;adjacent=[];read_count=0;unique_motion_frames=set()
    while True:
        data=proc.stdout.read(length)
        if not data:break
        if len(data)!=length:raise RuntimeError('Incomplete grayscale frame in motion proof.')
        if first is None:first=data
        unique_motion_frames.add(hashlib.sha256(data).digest())
        if previous is not None:adjacent.append(sum(abs(x-y) for x,y in zip(data,previous))/length)
        previous=data;read_count+=1
    error=proc.stderr.read().decode();proc.wait()
    if proc.returncode:raise RuntimeError(error)
    if read_count<2:raise RuntimeError('Export contains fewer than two decoded frames.')
    seam=sum(abs(x-y) for x,y in zip(first,previous))/length
    data=out.read_bytes();marker=b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00'
    sorted_adj=sorted(adjacent)
    if marker not in data:raise RuntimeError('GIF infinite-loop metadata was not found.')
    mp4=out.with_suffix('.mp4')
    report={'output':str(out),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
      'size':[s['width'],s['height']],'frames':frames,'duration_s':float(actual['format']['duration']),
      'fps_source':a.fps,'loop':0 if marker in data else 'unverified','analytic_period_s':period,
      'background_sha256':hashlib.sha256(bg.read_bytes()).hexdigest(),'background_size':[dims['width'],dims['height']],
      'motion_proof_size':[64,tiny_h],'decoded_motion_proof_frames':read_count,
      'unique_motion_proof_frames':len(unique_motion_frames),
      'adjacent_frame_mae_median':sorted_adj[len(sorted_adj)//2],
      'adjacent_frame_mae_range':[min(adjacent),max(adjacent)],'loop_seam_mae':seam,
      'contact_frames':indexes,'fireflies':len(lights),'rain_streaks':len(rain_specs),
      'geometry_protection_top_fraction':a.protect_top,'sway_px':a.sway_px,'seed':a.seed,
      'architecture_protection':f'geometric displacement zero above {a.protect_top:.1%} height; particles may overlay it',
      'frame_editing_tool':'FFmpeg only','render_mode':'opaque fixed background with local raster displacement and procedural particles',
      'mp4':{'path':str(mp4),'sha256':hashlib.sha256(mp4.read_bytes()).hexdigest(),'probe':probe(mp4)}}
    out.with_name(out.stem+'-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    work.joinpath('particle-spec.json').write_text(json.dumps({'fireflies':lights,'rain':rain_specs},indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
