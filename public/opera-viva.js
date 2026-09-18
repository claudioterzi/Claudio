(()=>{'use strict';
const C=OperaViva,$=id=>document.getElementById(id),canvas=$('art'),ctx=canvas.getContext('2d'),sourceCanvas=document.createElement('canvas');sourceCanvas.width=300;sourceCanvas.height=400;const sx=sourceCanvas.getContext('2d',{willReadFrequently:true});
let pixels=null,paths,pts,photo=null,loadCount=0,anim=0,start=0;
let state={title:$('title').value,gap:50,angle:.6446,source:'portrait',id:makeId()};
function makeId(){return 'CT-'+(crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+'-'+Math.random().toString(36).slice(2));}
function status(s){$('status').textContent=s;}
function buildSource(){
 sx.fillStyle='rgb(157,157,157)';sx.fillRect(0,0,300,400);
 if(state.source==='wave'){
  let im=sx.getImageData(0,0,300,400);for(let y=0;y<373;y++)for(let x=0;x<300;x++){let d=Math.hypot((x-150)/145,(y-185)/190),v=Math.round(157+43*Math.sin(d*16+x/50)*Math.exp(-d*d));let k=(y*300+x)*4;im.data[k]=im.data[k+1]=im.data[k+2]=v;im.data[k+3]=255;}sx.putImageData(im,0,0);
 }else if(state.source==='portrait'){
  const vals=atob(OPERA_VIVA_PORTRAIT);const im=sx.createImageData(300,400);for(let i=0;i<120000;i++){im.data[i*4]=im.data[i*4+1]=im.data[i*4+2]=vals.charCodeAt(i);im.data[i*4+3]=255;}sx.putImageData(im,0,0);
 }else if(photo){const scale=Math.min(276/photo.width,349/photo.height);sx.drawImage(photo,(300-photo.width*scale)/2,(373-photo.height*scale)/2,photo.width*scale,photo.height*scale);}
 pixels=sx.getImageData(0,0,300,400).data;
}
function sample(x,y){if(x<0||x>=600||y<0||y>=746)return .3848;let k=(Math.min(399,Math.floor(y/2))*300+Math.min(299,Math.floor(x/2)))*4;return 1-(.2126*pixels[k]+.7152*pixels[k+1]+.0722*pixels[k+2])/255;}
function pathFor(list){const path=new Path2D();for(const [x,y,r] of list){path.moveTo(x+r,y);path.arc(x,y,r,0,Math.PI*2);}return path;}
function rebuild(){pts=C.points(sample,state.gap);paths={front:pathFor(pts.front),rear:pathFor(pts.rear)};draw();$('gap-value').value=state.gap+' mm';$('angle-value').value=state.angle.toFixed(4).replace('.',',')+'°';$('metric').textContent='Passo 4,50 mm · scala posteriore '+(1+state.gap/2500).toFixed(3)+' · circa '+(4.5*(2500+state.gap)/state.gap/10).toFixed(1)+' cm per ciclo orizzontale.';}
function draw(){const eye=+$('eye').value,k=2500/(2500+state.gap),shift=state.gap*eye/(2500+state.gap),view=$('view').value;ctx.setTransform(2,0,0,2,0,0);ctx.fillStyle='#eeeae0';ctx.fillRect(0,0,600,800);ctx.save();ctx.beginPath();ctx.rect(0,0,600,746);ctx.clip();ctx.fillStyle='#08080b';if(view!=='front'){ctx.save();ctx.translate(300+shift,400);ctx.scale(k,k);ctx.rotate(state.angle*Math.PI/180);ctx.translate(-300,-400);ctx.fill(paths.rear);ctx.restore();}if(view!=='rear')ctx.fill(paths.front);ctx.restore();ctx.save();ctx.translate(444,754);ctx.scale(.62,.62);ctx.strokeStyle='#171519';ctx.lineWidth=2.1;ctx.lineCap='round';ctx.lineJoin='round';ctx.stroke(new Path2D(C.SIGN));ctx.restore();$('eye-value').value=(eye/10).toFixed(1)+' cm';}
function stop(){cancelAnimationFrame(anim);anim=0;start=0;$('play').textContent='Simula passaggio';}
$('play').onclick=()=>{if(anim){stop();return;}function frame(t){if(!start)start=t;let u=Math.min((t-start)/8000,1);$('eye').value=-600+1200*u;draw();if(u<1)anim=requestAnimationFrame(frame);else stop();} $('play').textContent='Ferma';anim=requestAnimationFrame(frame);};
$('eye').oninput=()=>{stop();draw();};$('view').onchange=()=>{stop();draw();};
for(const id of ['gap','angle'])$(id).oninput=()=>{stop();state[id]=+$(id).value;state.id=makeId();rebuild();};
$('preset').onchange=()=>{stop();const g={balanced:50,energetic:75,soft:30}[$('preset').value];state.gap=g;$('gap').value=g;state.id=makeId();rebuild();};
$('source').onchange=()=>{stop();state.source=$('source').value;state.id=makeId();state.title=state.source==='wave'?'Onde · Studio cinetico':state.source==='portrait'?'Raffaello · Studio 01':'La mia opera';$('title').value=state.title;$('workname').textContent=state.title;buildSource();rebuild();};
$('title').oninput=()=>{state.title=$('title').value.trim()||'Opera senza titolo';$('workname').textContent=state.title;state.id=makeId();};
$('photo').onchange=()=>{const f=$('photo').files[0];if(!f)return;const token=++loadCount;if(!['image/png','image/jpeg','image/webp'].includes(f.type)||f.size>20*1024*1024){status('Scegli un PNG, JPEG o WebP fino a 20 MB.');return;}const url=URL.createObjectURL(f),im=new Image();im.onload=()=>{URL.revokeObjectURL(url);if(token!==loadCount)return;stop();photo=im;$('source').querySelector('[value=upload]').disabled=false;$('source').value='upload';$('source').onchange();status('Fotografia inserita intera. Nessun invio al server.');};im.onerror=()=>{URL.revokeObjectURL(url);status('Immagine non leggibile. Prova un PNG o JPEG.');};im.src=url;};
function save(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);status('Esportato: '+name);}
const stem=()=>state.title.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-zA-Z0-9_-]+/g,'-').slice(0,60)+'_CTerzi';
for(const kind of ['front','rear'])$(kind).onclick=()=>save(new Blob([C.svg(kind,pts,state)],{type:'image/svg+xml'}),stem()+'_'+(kind==='front'?'lastra-1':'lastra-2')+'.svg');
$('png').onclick=()=>{stop();draw();canvas.toBlob(b=>{if(b)save(b,stem()+'_anteprima.png');else status('Esportazione non riuscita.');},'image/png');};
$('project').onclick=()=>{const data=C.project(state);data.sampled_source={width:300,height:400,grayscale_base64:btoa(Array.from({length:120000},(_,i)=>String.fromCharCode(Math.round(.2126*pixels[i*4]+.7152*pixels[i*4+1]+.0722*pixels[i*4+2]))).join(''))};save(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),stem()+'_progetto.json');};
$('signature').innerHTML='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 205 70">'+C.signature(0,0,1)+'</svg>';
buildSource();rebuild();
})();
