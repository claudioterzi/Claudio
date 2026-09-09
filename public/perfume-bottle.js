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
  async function render(perfume, variant=0) {
    const T=await (library ||= import('/vendor/three.module.min.js'));
    const spec=design(perfume,variant);
    const renderer=new T.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'low-power'});
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
    const profile=variant?[[0,-1.24],[w*.58,-1.24],[w*.85,-1.12],[w,-.7],[w*.98,.05],[w*.83,.53],[.3,.91],[.23,1.08],[0,1.08]]:
      [[0,-1.24],[w*.85,-1.24],[w,-1.12],[w,spec.shoulder],[w*.84,.82],[.26,1.03],[.24,1.09],[0,1.09]];
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
    try {renderer.render(scene,camera);return {url:renderer.domElement.toDataURL('image/png'),spec};}
    finally {scene.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});env.dispose();environment.dispose();pmrem.dispose();renderer.dispose();}
  }
  root.TerziBottle={design,render};
  if(typeof module!=='undefined'&&module.exports)module.exports={design};
})(typeof window!=='undefined'?window:globalThis);
