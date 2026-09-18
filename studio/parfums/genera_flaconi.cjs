/* Book illustrations from the existing Terzi 3D surface renderer.
 * Concept and direction: Claudio Terzi. These are aesthetic studies, not CAD.
 * Run: node studio/parfums/genera_flaconi.cjs
 * Dependency: @napi-rs/canvas (also resolved from CODEX_PRIMARY_RUNTIME_NODE_MODULES).
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const {design,renderCompatible}=require('../../public/perfume-bottle.js');
const resolvePackage=name=>require(require.resolve(name,{paths:[root,process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES].filter(Boolean)}));
const hex=s=>parseInt(s.replace('#',''),16);
const xml=s=>String(s).replace(/[<>&"']/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&apos;'}[c]));
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const finish={
  Agrumata:{cap:0xb58b51,metal:0xbca36c},Floreale:{cap:0xd5c9d0,metal:0xc0b496},
  Verde:{cap:0x89765b,metal:0xaaa38b},Acquatica:{cap:0xb0bac0,metal:0xa2afb5},
  Legnosa:{cap:0x92633a,metal:0xa38259},Orientale:{cap:0x967239,metal:0xb39052},
  Speziata:{cap:0x282526,metal:0xac7d54},Gourmand:{cap:0xe1d2b6,metal:0xb9a07b}
};
function bookDesign(p){
  const recipe=p.ricetta.map(r=>[r.n,r.parti,r.livello,!!r.micro]).sort((a,b)=>a[0]-b[0]);
  const fingerprint=hash(JSON.stringify(recipe));
  const u=i=>parseInt(fingerprint.slice(i*2,i*2+2),16)/255;
  const layer=level=>p.ricetta.filter(r=>r.livello===level).reduce((s,r)=>s+r.parti,0)/100;
  const pk=p.packaging, style=finish[p.famiglia];
  const spec={...design({fam:p.famiglia,formula_code:fingerprint}),
    version:'terzi-book-3d-1',fingerprint,shape:pk.forma,color:hex(pk.palette.liquido),
    capColor:style.cap,metal:style.metal,bands:1+(Math.floor(u(9)*2)),
    width:(pk.forma==='slanciata'?.52:pk.forma==='tonda'?.88:.74)+u(0)*.13,
    shoulder:.24+layer('cuore')*.6+u(1)*.15,
    capRadius:.27+u(2)*.13,capHeight:.24+u(3)*.18,
    facets:pk.forma==='quadrata'?[4,8,12][Math.floor(u(4)*2.999)]:[32,48,64][Math.floor(u(4)*2.999)],
    capSegments:pk.forma==='quadrata'?8:48,
    rotation:(u(5)*9-4.5)*Math.PI/180,
  };
  const w=spec.width,neck=.22+u(6)*.045;
  const base=.75+layer('fondo')*.3+u(7)*.08;
  const waist=.85+u(8)*.12;
  if(pk.forma==='slanciata')spec.profile=[[0,-1.24],[w*base,-1.24],[w,-1.08],[w*waist,.12],[w*.86,spec.shoulder+.24],[neck,.95],[neck,1.09],[0,1.09]];
  if(pk.forma==='quadrata')spec.profile=[[0,-1.24],[w*.96,-1.24],[w,-1.12],[w,spec.shoulder+.15],[w*.9,.76],[neck,1.03],[neck,1.09],[0,1.09]];
  if(pk.forma==='tonda'){
    spec.profile=[[0,-1.24],[w*.38,-1.24]];
    for(let i=1;i<=16;i++){const t=i/17*Math.PI;spec.profile.push([w*Math.sin(t)*(.97+u(10)*.03),-1.2+2.18*i/17]);}
    spec.profile.push([neck,1.02],[neck,1.09],[0,1.09]);
  }
  if(pk.forma==='anfora')spec.profile=[[0,-1.24],[w*base*.68,-1.24],[w*.76,-1.12],[w,-.65],[w*waist,.14],[w*.67,.7],[neck,.98],[neck,1.09],[0,1.09]];
  if(p.famiglia==='Floreale'){
    spec.capProfile=[[0,1.09]];
    for(let i=0;i<=12;i++){const t=i*Math.PI/12;spec.capProfile.push([spec.capRadius*Math.sin(t),1.09+spec.capHeight*(1-Math.cos(t))/2]);}
    spec.capProfile.push([0,1.09+spec.capHeight]);spec.bands=0;
  }else spec.capProfile=[[0,1.09],[spec.capRadius,1.09],[spec.capRadius*(.91+u(11)*.18),1.09+spec.capHeight],[0,1.09+spec.capHeight]];
  spec.accents=['testa','cuore','fondo'].map(level=>p.ricetta.filter(r=>r.livello===level).sort((a,b)=>b.parti-a.parti)[0]?.nome).filter(Boolean);
  return spec;
}
function label(ctx,p,spec){
  const width=Math.min(365,spec.width*480),left=600-width/2,top=spec.shape==='tonda'?520:622,height=235;
  ctx.fillStyle='#f4ecd9';ctx.fillRect(left,top,width,height);
  ctx.strokeStyle='#947b48';ctx.lineWidth=2;ctx.strokeRect(left+8,top+8,width-16,height-16);
  ctx.textAlign='center';ctx.fillStyle='#655333';ctx.font='20px serif';ctx.fillText('TERZI PARFUMS',600,top+38);
  let size=31,lines=[];
  do{
    ctx.font=size+'px serif';lines=[''];
    for(const word of p.nome.split(' ')){const last=lines.length-1,next=(lines[last]+' '+word).trim();if(ctx.measureText(next).width>width-34&&lines[last])lines.push(word);else lines[last]=next;}
    if(lines.length<=3&&lines.every(t=>ctx.measureText(t).width<=width-34))break;size--;
  }while(size>18);
  ctx.fillStyle='#322d22';lines.forEach((text,i)=>ctx.fillText(text,600,top+77+i*(size+4)));
  ctx.font='22px serif';ctx.fillText('N° '+String(p.numero).padStart(3,'0'),600,top+183);
  ctx.font='italic 25px serif';ctx.fillText('C.Terzi',600,top+217);
}
async function generate(){
  const {createCanvas}=resolvePackage('@napi-rs/canvas');
  const perfumes=JSON.parse(fs.readFileSync(path.join(__dirname,'parfums_400.json'),'utf8')).parfums;
  const out=path.join(root,'public/images/flaconi-400');fs.mkdirSync(out,{recursive:true});
  const records=[];
  for(const p of perfumes){
    const spec=bookDesign(p),canvas=createCanvas(1200,1200);
    renderCompatible(spec,0,{paper:true,canvas});label(canvas.getContext('2d'),p,spec);
    const frame=createCanvas(900,1200);frame.getContext('2d').drawImage(canvas,150,0,900,1200,0,0,900,1200);
    const jpeg=await frame.encode('jpeg',86);
    const id=String(p.numero).padStart(3,'0'),file=`P${id}.svg`;
    // A self-contained SVG image container; the artwork is the existing CPU 3D raster,
    // not hand-drawn SVG geometry. JPEG keeps printing and offline export portable.
    const svg=`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 900 1200" width="900" height="1200" role="img" aria-labelledby="title desc"><title id="title">${xml(p.nome)} — N° ${id}</title><desc id="desc">Studio di flacone da geometria 3D. ${xml(p.packaging.flacone)}; tappo ${xml(p.packaging.tappo)}. Concept Claudio Terzi, C.Terzi.</desc><image width="900" height="1200" xlink:href="data:image/jpeg;base64,${jpeg.toString('base64')}"/></svg>\n`;
    fs.writeFileSync(path.join(out,file),svg);
    records.push({numero:p.numero,nome:p.nome,famiglia:p.famiglia,src:`images/flaconi-400/${file}`,sha256:hash(svg),recipe_fingerprint:spec.fingerprint,geometry_fingerprint:hash(JSON.stringify({profile:spec.profile,width:spec.width,capRadius:spec.capRadius,capHeight:spec.capHeight,facets:spec.facets,rotation:spec.rotation})),design:spec,kind:'illustrazione da geometria 3D',attribution:'Concept e direzione: Claudio Terzi · C.Terzi'});
    if(p.numero%50===0)console.log(`${p.numero}/400 flaconi salvati`);
  }
  const manifest={version:'1.0',date:'2026-09-10',count:records.length,method:'Illustrazioni da geometrie 3D individuali; proposte estetiche, non disegni di fabbricazione.',perfumes:records};
  fs.writeFileSync(path.join(__dirname,'flaconi_400.json'),JSON.stringify(manifest,null,2)+'\n');
  if(new Set(records.map(x=>x.geometry_fingerprint)).size!==400)throw Error('Geometrie duplicate');
  if(new Set(records.map(x=>x.sha256)).size!==400)throw Error('Immagini duplicate');
  console.log('400 geometrie e 400 immagini distinte; manifesto salvato.');
}
module.exports={bookDesign};
if(require.main===module)generate().catch(e=>{console.error(e);process.exitCode=1;});
