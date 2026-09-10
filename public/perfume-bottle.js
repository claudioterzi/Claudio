/* Flaconi generativi 3D · Concept e direzione Claudio Terzi · © 2026. */
(function (root) {
  'use strict';
  const colors = {Agrumata:0xd5a638,Floreale:0xb494bc,Verde:0x477968,Acquatica:0x428ca1,
    Legnosa:0xa77442,Orientale:0xb27931,Speziata:0x913d40,Gourmand:0xb68c65};
  function design(perfume, variant = 0) {
    if (![0,1].includes(variant)) throw Error('Versione non valida');
    const identity = perfume.formula_code || perfume.flacone?.recipe_fingerprint || JSON.stringify(perfume.ricetta || []);
    let seed=2166136261;for(const ch of identity)seed=Math.imul(seed^ch.charCodeAt(0),16777619)>>>0;
    const u = n => ((seed >>> n) & 255)/255;
    return {version:'terzi-3d-1',identity,variant,seed,
      label:variant?'Essenza':'Scultura',color:colors[perfume.fam]||colors.Orientale,
      facets:variant?64:[6,8,10,12][seed%4],width:.78+u(3)*.15,
      shoulder:.42+u(12)*.33,capRadius:.32+u(7)*.12,
      capHeight:.3+u(17)*.12,rotation:(seed%12)*Math.PI/180,
      bands:2+(seed%4),metal:variant?0xd3c5a4:0xb89b63};
  }
  let library;
  function bottleProfile(spec,variant) {
    const w=spec.width;
    return variant?[[0,-1.24],[w*.58,-1.24],[w*.85,-1.12],[w,-.7],[w*.98,.05],[w*.83,.53],[.3,.91],[.23,1.08],[0,1.08]]:
      [[0,-1.24],[w*.85,-1.24],[w,-1.12],[w,spec.shoulder],[w*.84,.82],[.26,1.03],[.24,1.09],[0,1.09]];
  }
  // A CPU projection of the same 3D surfaces keeps the concept available without WebGL.
  // It is an illustration with simplified lighting, not a photographic ray trace.
  function renderCompatible(spec,variant,options={}) {
    const canvas=options.canvas||document.createElement('canvas');canvas.width=canvas.height=1200;
    const ctx=canvas.getContext('2d');
    if(!ctx)throw Error('Canvas non disponibile');
    if(options.paper){ctx.fillStyle='#f6f2e9';ctx.fillRect(0,0,1200,1200);}else{
    const bg=ctx.createLinearGradient(0,0,1200,1200);bg.addColorStop(0,variant?'#34444d':'#233743');bg.addColorStop(.55,'#0b1119');bg.addColorStop(1,'#080a10');ctx.fillStyle=bg;ctx.fillRect(0,0,1200,1200);
    const halo=ctx.createRadialGradient(335,330,25,420,530,600);halo.addColorStop(0,'#c4a56a36');halo.addColorStop(1,'#c4a56a00');ctx.fillStyle=halo;ctx.fillRect(0,0,1200,1200);
    const shadow=ctx.createRadialGradient(600,1020,50,600,1020,420);shadow.addColorStop(0,'#000d');shadow.addColorStop(1,'#0000');ctx.fillStyle=shadow;ctx.fillRect(100,850,1000,350);
    }
    if(options.paper){ctx.save();ctx.translate(600,1010);ctx.scale(1,.18);const sh=ctx.createRadialGradient(0,0,35,0,0,420);sh.addColorStop(0,'#41372b55');sh.addColorStop(1,'#41372b00');ctx.fillStyle=sh;ctx.fillRect(-450,-450,900,900);ctx.restore();}
    const project=v=>{const y=v[1]-.04,z=v[2]-7.2;const yy=y*.999-z*.039,zz=y*.039+z*.999;return [600+v[0]*2100/-zz,590-yy*2100/-zz];};
    const normalize=v=>{const l=Math.hypot(...v)||1;return v.map(x=>x/l);};
    const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
    const polys=[];
    function surface(profile,segments,rotation,hex,material) {
      for(let j=0;j<profile.length-1;j++)for(let i=0;i<segments;i++) {
        const a=i*2*Math.PI/segments+rotation,b=(i+1)*2*Math.PI/segments+rotation;
        const v=(p,t)=>[Math.sin(t)*p[0],p[1],Math.cos(t)*p[0]];
        const points=[v(profile[j],a),v(profile[j],b),v(profile[j+1],b),v(profile[j+1],a)];
        const mid=points[0].map((_,k)=>points.reduce((s,p)=>s+p[k],0)/4);
        const normal=normalize([Math.sin((a+b)/2)*(profile[j+1][1]-profile[j][1]),profile[j][0]-profile[j+1][0],Math.cos((a+b)/2)*(profile[j+1][1]-profile[j][1])]);
        const view=normalize([-mid[0],.32-mid[1],7.2-mid[2]]);
        if(dot(normal,view)<=0)continue;
        const light=normalize([-3,4,5]),half=normalize(light.map((x,k)=>x+view[k]));
        const lambert=Math.max(0,dot(normal,light)),shine=Math.pow(Math.max(0,dot(normal,half)),material==='glass'?34:18);
        const edge=Math.pow(1-Math.max(0,dot(normal,view)),2);
        const base=[(hex>>16)&255,(hex>>8)&255,hex&255];
        const strength=material==='glass'?.22+lambert*.66:.2+lambert*.95;
        const rgb=base.map((x,k)=>Math.min(255,Math.round(x*strength+shine*(material==='glass'?185:95)+edge*[88,101,104][k])));
        polys.push({points,depth:mid[2],rgb,fill:'rgb('+rgb.join(',')+')',edge:material==='glass'});
      }
    }
    if(!options.paper)surface([[0,-1.43],[1.35,-1.43],[1.24,-1.28],[0,-1.28]],96,0,0x34414a,'metal');
    surface(spec.profile||bottleProfile(spec,variant),spec.facets,variant?0:Math.PI/spec.facets+spec.rotation,spec.color,'glass');
    const w=spec.width;
    const foot=options.paper?spec.profile[1][0]:w*.95;
    surface([[0,-1.27],[foot*.98,-1.27],[foot,-1.215],[0,-1.215]],spec.facets,0,spec.metal,'metal');
    surface([[0,.97],[.27,.97],[.245,1.1],[0,1.1]],48,0,spec.metal,'metal');
    surface(spec.capProfile||[[0,1.15],[spec.capRadius,1.15],[spec.capRadius*(variant?1.25:1),1.15+spec.capHeight],[0,1.15+spec.capHeight]],spec.capSegments||(variant?64:spec.facets),spec.rotation,spec.capColor??(variant?spec.metal:0x34424b),'metal');
    for(let i=0;i<spec.bands;i++) {
      const y=1.195+i*.037;
      surface([[spec.capRadius+.006,y],[spec.capRadius+.006,y+.008]],64,0,spec.metal,'metal');
    }
    polys.sort((a,b)=>a.depth-b.depth);
    const left=project([-w,0,0])[0],right=project([w,0,0])[0];
    const reflection=ctx.createLinearGradient(left,0,right,0);
    for(const [at,alpha] of [[0,0],[.045,.9],[.065,.08],[.13,.02],[.18,.65],[.205,.03],[.55,0],[.77,.015],[.88,.68],[.904,.025],[.98,.5],[1,0]])reflection.addColorStop(at,'rgba(255,241,204,'+alpha+')');
    for(const p of polys){const points=p.points.map(project);ctx.beginPath();points.forEach((v,i)=>i?ctx.lineTo(...v):ctx.moveTo(...v));ctx.closePath();
      if(p.edge){const gradient=ctx.createLinearGradient(0,220,0,960);const tone=(scale,extra=0)=>'rgb('+p.rgb.map(x=>Math.min(255,Math.round(x*scale+extra))).join(',')+')';gradient.addColorStop(0,tone(1.15,22));gradient.addColorStop(.23,tone(.57));gradient.addColorStop(.6,tone(.82));gradient.addColorStop(.87,tone(.39));gradient.addColorStop(1,tone(1.25,32));ctx.fillStyle=gradient;}else ctx.fillStyle=p.fill;
      ctx.fill();ctx.strokeStyle=p.fill;ctx.lineWidth=.5;ctx.stroke();
      if(p.edge){ctx.save();ctx.clip();ctx.globalCompositeOperation='screen';ctx.fillStyle=reflection;ctx.fillRect(left-20,100,right-left+40,950);ctx.restore();}
    }
    return {url:canvas.toDataURL('image/png'),spec:{...spec,renderer:'cpu-illustration'}};
  }
  async function render(perfume, variant=0) {
    const spec=design(perfume,variant);
    const canvas=document.createElement('canvas');let context;
    try {context=canvas.getContext('webgl2',{antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'low-power'});}catch (_) {}
    if(!context)return renderCompatible(spec,variant);
    let T;try {T=await (library ||= import('/vendor/three.module.min.js'));}catch (_) {return renderCompatible(spec,variant);}
    const renderer=new T.WebGLRenderer({canvas,context,antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'low-power'});
    renderer.setSize(1200,1200);renderer.setPixelRatio(1);
    renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
    renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
    const scene=new T.Scene();scene.background=new T.Color(variant?0x171e25:0x0d1319);
    const camera=new T.PerspectiveCamera(31,1,.1,50);camera.position.set(0,.3,7.2);camera.lookAt(0,.02,0);
    const studio=document.createElement('canvas');studio.width=1024;studio.height=512;
    const c=studio.getContext('2d');const g=c.createLinearGradient(0,0,0,512);
    g.addColorStop(0,'#d4d1c9');g.addColorStop(.45,'#67635d');g.addColorStop(.6,'#252829');g.addColorStop(1,'#08090c');
    c.fillStyle=g;c.fillRect(0,0,1024,512);
    for(const [x,w] of [[80,95],[480,170],[900,38]]){c.fillStyle='#fff8ed';c.fillRect(x,55,w,330);}
    const environment=new T.CanvasTexture(studio);environment.mapping=T.EquirectangularReflectionMapping;environment.colorSpace=T.SRGBColorSpace;
    const pmrem=new T.PMREMGenerator(renderer),env=pmrem.fromEquirectangular(environment);scene.environment=env.texture;
    scene.add(new T.HemisphereLight(0xfaf3e3,0x243343,2));
    const key=new T.DirectionalLight(0xffedd4,5);key.position.set(-3,5,5);key.castShadow=true;key.shadow.mapSize.set(1024,1024);scene.add(key);
    const rim=new T.DirectionalLight(0xa9cbff,3);rim.position.set(3,2,-2);scene.add(rim);
    const glass=new T.MeshPhysicalMaterial({color:spec.color,metalness:0,roughness:.12,transmission:.72,
      thickness:.8,ior:1.5,attenuationColor:spec.color,attenuationDistance:2,clearcoat:1,envMapIntensity:1.4,
      flatShading:!variant});
    const metal=new T.MeshStandardMaterial({color:spec.metal,metalness:.88,roughness:.25});
    const dark=new T.MeshStandardMaterial({color:0x141c23,metalness:.3,roughness:.28});
    const w=spec.width;
    const profile=bottleProfile(spec,variant);
    const body=new T.Mesh(new T.LatheGeometry(profile.map(p=>new T.Vector2(...p)),spec.facets),glass);
    body.rotation.y=variant?0:Math.PI/spec.facets+spec.rotation;body.castShadow=true;body.receiveShadow=true;scene.add(body);
    const neck=new T.Mesh(new T.CylinderGeometry(.245,.27,.13,48),metal);neck.position.y=1.035;scene.add(neck);
    const cap=new T.Mesh(new T.CylinderGeometry(spec.capRadius*(variant?1.25:1),spec.capRadius,spec.capHeight,variant?64:spec.facets),variant?metal:dark);
    cap.position.y=1.15+spec.capHeight/2;cap.rotation.y=body.rotation.y;cap.castShadow=true;scene.add(cap);
    for(let i=0;i<spec.bands;i++){
      const ring=new T.Mesh(new T.TorusGeometry(spec.capRadius+.006,.008,8,64),metal);
      ring.rotation.x=Math.PI/2;ring.position.y=cap.position.y-spec.capHeight/2+.045+i*.037;scene.add(ring);
    }
    const foot=new T.Mesh(new T.CylinderGeometry(w*.95,w*.93,.055,spec.facets),metal);foot.position.y=-1.235;foot.rotation.y=body.rotation.y;scene.add(foot);
    const plinth=new T.Mesh(new T.CylinderGeometry(1.24,1.35,.15,96),new T.MeshStandardMaterial({color:0x171d23,roughness:.42,metalness:.35}));
    plinth.position.y=-1.35;plinth.receiveShadow=true;scene.add(plinth);
    const floor=new T.Mesh(new T.PlaneGeometry(30,30),new T.MeshStandardMaterial({color:0x151e27,roughness:.48,metalness:.2}));
    floor.rotation.x=-Math.PI/2;floor.position.y=-1.43;floor.receiveShadow=true;scene.add(floor);
    try {renderer.render(scene,camera);return {url:renderer.domElement.toDataURL('image/png'),spec:{...spec,renderer:'webgl'}};}
    finally {scene.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});env.dispose();environment.dispose();pmrem.dispose();renderer.dispose();renderer.forceContextLoss();}
  }
  root.TerziBottle={design,render};
  if(typeof module!=='undefined'&&module.exports)module.exports={design,renderCompatible};
})(typeof window!=='undefined'?window:globalThis);
