/* Small images display the canonical state; they never determine a reading. */
(function(root){
  'use strict';
  const rotations=Object.freeze({nord:0,est:-90,sud:180,ovest:90});
  function resolve(card){
    const id=Number(card.id);
    if(!Number.isInteger(id)||id<1||id>74||!Object.hasOwn(rotations,card.asse))return null;
    if(card.polarita!=='luce'&&card.polarita!=='ombra')return null;
    const base='/images/alpha74/'+String(id).padStart(2,'0')+'/'+card.polarita;
    return Object.freeze({id,thumbnail:base+'-160.webp',detail:base+'-640.webp',rotation:rotations[card.asse]});
  }
  const api=Object.freeze({resolve});
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.Alpha74Art=api;
})(typeof globalThis!=='undefined'?globalThis:this);
