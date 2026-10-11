/* Opera Viva · C.Terzi. Geometria condivisa fra anteprima ed esportazione. */
(function(root){'use strict';
 const W=600,H=800,P=4.5,M=18,D=2500,NY=Math.ceil((H+2*M)/P),NX=Math.ceil((W+2*M)/P);
 // Firma disegnata per il progetto, non facsimile di una firma autografa.
 const SIGN='M40 13 C25 -1 3 18 5 37 C7 53 32 52 42 35 M47 46 L48 46 M57 16 C77 10 98 7 105 12 M83 11 C77 26 68 50 70 53 M91 37 C115 34 108 23 98 29 C85 39 92 52 106 45 L115 35 C124 17 124 28 118 43 C126 26 134 24 136 31 M134 31 L154 28 L134 48 L157 43 M164 28 L156 43 C153 52 165 46 172 39 M168 19 L169 19 M21 63 C70 49 138 61 199 46';
 const round=n=>Number(n.toFixed(4));
 const esc=t=>String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
 function signature(x=444,y=754,size=.62){return `<g aria-label="C.Terzi" transform="translate(${x} ${y}) scale(${size})"><title>C.Terzi</title><path d="${SIGN}" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/></g>`;}
 function points(sample,gap=50){const front=[],rear=[],sc=1+gap/D;for(let j=0;j<NY;j++)for(let i=0;i<NX;i++){
   const x=(i+.5)*P-M,y=(j+.5)*P-M;
   if(y<746){const coverage=sample(x,y);const r=P*Math.sqrt(Math.max(.005,Math.min(.77,coverage))/Math.PI);rear.push([300+(x-300)*sc,400+(y-400)*sc,r*sc]);}
 }
 for(let j=0;j<Math.ceil(746/P);j++)for(let i=0;i<Math.ceil(W/P);i++)front.push([(i+.5)*P,(j+.5)*P,1.575]);
 return {front,rear};}
 function svg(kind,pts,state){let rear=kind==='rear',w=rear?636:600,h=rear?836:800,off=rear?18:0;
 let s=`<svg xmlns="http://www.w3.org/2000/svg" width="${w}mm" height="${h}mm" viewBox="0 0 ${w} ${h}"><title>${esc(state.title)} — C.Terzi — ${rear?'lastra posteriore':'lastra anteriore'}</title><desc>Claudio Terzi. Provino sperimentale. ID ${esc(state.id)}. Intercapedine ${state.gap} mm. Ruotare lastra posteriore ${state.angle} gradi. Distanza nominale 2500 mm. Scala posteriore ${1+state.gap/D}. Firma sulla lastra anteriore.</desc><g fill="#000">`;
 for(const [x,y,r] of pts[kind])s+=`<circle cx="${round(x+off)}" cy="${round(y+off)}" r="${round(r)}"/>`;
 s+='</g>';if(!rear)s+=`<g color="#000">${signature()}</g>`;return s+'</svg>';}
 function project(state){return {schema:'opera-viva/1.0',id:state.id,title:state.title,author:'Claudio Terzi',signature:'C.Terzi',source:state.source,created_at:new Date().toISOString(),geometry:{width_mm:W,height_mm:H,front_pitch_mm:P,front_dot_diameter_mm:3.15,gap_mm:state.gap,rotation_deg:state.angle,observer_distance_mm:D,rear_scale:1+state.gap/D,rear_pitch_mm:P*(1+state.gap/D),rear_panel_mm:[636,836],signature_band_mm:54},status:'provino_non_validato',original_70_percent_test:false};}
 const api={W,H,P,M,D,NX,NY,SIGN,points,svg,project,signature};root.OperaViva=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
