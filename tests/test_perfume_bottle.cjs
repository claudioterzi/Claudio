const assert = require('node:assert/strict');
const {design} = require('../public/perfume-bottle.js');
const a = {fam:'Legnosa',ricetta:[['Cedro',21,100,'fondo',false]]};
const b = {fam:'Floreale',ricetta:[['Rosa',22,100,'cuore',false]]};
assert.deepEqual(design(a),design(a));
assert.deepEqual(design(a),design({...a,customer:'Nome riservato'}));
assert.notEqual(design(a).seed,design(b).seed);
assert.notEqual(design(a).facets,design(a,1).facets);
assert.notEqual(design(a).metal,design(a,1).metal);
assert.throws(()=>design(a,2));
for(let i=1;i<=300;i++) {
  for(const v of [0,1]) {
    const s=design({ricetta:[['Materia',i,100,'fondo',false]]},v);
    assert.ok(s.width>=.78&&s.width<=.93);
    assert.ok(s.capHeight>=.3&&s.capHeight<=.42);
    assert.ok(s.bands>=2&&s.bands<=5);
  }
}
console.log('Flaconi: firma riproducibile, varianti distinte, nome privato escluso, geometria valida.');
