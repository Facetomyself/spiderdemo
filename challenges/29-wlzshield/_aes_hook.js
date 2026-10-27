t.AES=e._createHelper(v)}(),(function(a){
try{
  if(e.enc&&e.enc.Base64&&typeof e.enc.Base64.stringify==="function"&&!e.enc.Base64.stringify.__wrapped){
    var stringify=e.enc.Base64.stringify;
    var wrappedStringify=function(wordArray){
      var out=stringify.apply(this,arguments);
      try{
        var n=wordArray&&wordArray.sigBytes||0;
        var bag=globalThis.__b64n||(globalThis.__b64n=[]);
        if(bag.length<12)bag.push(n);
        if(n===12&&wordArray&&wordArray.words&&!globalThis.__b12){
          var bytes=[];
          for(var i=0;i<12;i++){
            var word=wordArray.words[i>>>2]>>>0;
            bytes.push((word>>>(24-(i%4)*8))&255);
          }
          globalThis.__b12=bytes;
        }
      }catch(_error){}
      return out;
    };
    wrappedStringify.__wrapped=1;
    e.enc.Base64.stringify=wrappedStringify;
  }
  var WA=e.lib&&e.lib.WordArray;
  if(WA&&typeof WA.random==="function"&&!WA.random.__wrapped){
    var random=WA.random;
    var wrapped=function(n){var out=random.call(this,n);var bag=globalThis.__rnd||(globalThis.__rnd=[]);if(bag.length<8)bag.push("r"+n);return out;};
    wrapped.__wrapped=1;
    WA.random=wrapped;
  }
  ["MD5","SHA1","SHA256","SHA512","HmacMD5","HmacSHA1","HmacSHA256","PBKDF2","EvpKDF"].forEach(function(name){
    if(typeof e[name]!=="function"||e[name].__wrapped)return;
    var orig=e[name];
    var wrappedHash=function(value){
      var bag=globalThis.__kdf||(globalThis.__kdf=[]);
      if(bag.length<16){
        var kind=value==null?"null":typeof value==="string"?"s"+value.length:(value&&value.sigBytes?"w"+value.sigBytes:typeof value);
        bag.push(name+":"+kind);
      }
      return orig.apply(this,arguments);
    };
    wrappedHash.__wrapped=1;
    e[name]=wrappedHash;
  });
}catch(_error){}
function byteAt(w,i){var word=w.words[i>>>2]>>>0;return (word>>>(24-(i%4)*8))&255;}
function head(w){if(!w||!w.words||!w.words.length)return "none";return byteAt(w,0)+"."+byteAt(w,1)+"."+byteAt(w,2)+"."+byteAt(w,3);}
function findAscii(w, ascii){var n=w.sigBytes||0;outer:for(var i=0;i+ascii.length<=n;i++){for(var k=0;k<ascii.length;k++)if(byteAt(w,i+k)!==ascii.charCodeAt(k))continue outer;return i;}return -1;}
function findBrace(w){var payload=findAscii(w, '{"payload"');if(payload>=0)return payload;var session=findAscii(w, '{"sessionId"');if(session>=0)return session;return findAscii(w, '{"');}
function decodeTail(w,start){var n=w.sigBytes||0,bytes=new Uint8Array(n-start);for(var i=start;i<n;i++)bytes[i-start]=byteAt(w,i);return new TextDecoder().decode(bytes);}
function writeBytes(w,bytes){var words=new Array(Math.ceil(bytes.length/4));for(var i=0;i<words.length;i++)words[i]=0;for(var j=0;j<bytes.length;j++)words[j>>>2]|=bytes[j]<<((3-(j%4))*8);w.words=words;w.sigBytes=bytes.length;if(typeof w.clamp==="function")w.clamp();}
function repackBytes(w){
  if(!globalThis.__aesRepack)return "off";
  var src=w.words, n=src.length;
  if(n<4)return "short";
  if((src[0]&255)!==31||(src[1]&255)!==139)return "nomagic w0"+(src[0]>>>0);
  var bytes=new Uint8Array(n);
  for(var i=0;i<n;i++)bytes[i]=src[i]&255;
  writeBytes(w, bytes);
  var shape = typeof globalThis.__gunzipShape === "function" ? globalThis.__gunzipShape(bytes) : "noshape";
  return "repack"+n+" "+shape;
}
function calmMessage(w){
  if(!globalThis.__aesCalm)return "off";
  try{
    var start=findBrace(w);if(start<0)return "nobrace";
    var text=decodeTail(w,start);var end=text.lastIndexOf("}");if(end<0)return "noend";
    var obj=JSON.parse(text.slice(0,end+1));
    var risks=obj&&obj.risks?obj.risks:(obj&&obj.payload&&obj.payload.risks);
    if(!Array.isArray(risks))return "norisk";
    for(var i=0;i<risks.length;i++)if(risks[i]&&typeof risks[i]==="object")risks[i].detected=false;
    var next=JSON.stringify(obj);
    var header=new Uint8Array(start);for(var h=0;h<start;h++)header[h]=byteAt(w,h);
    var body=new TextEncoder().encode(next);
    var merged=new Uint8Array(header.length+body.length);
    merged.set(header,0);merged.set(body,header.length);
    writeBytes(w,merged);
    return "calmed"+risks.length+" body"+body.length;
  }catch(_error){return "fail";}
}
var encrypt=a.encrypt;
a.encrypt=function(m,k,c){
  var rec=globalThis.__aesRec||(globalThis.__aesRec={n:0,msg:"",key:"",cfg:"",out:"",head:"",chead:"",scan:"",calm:""});
  rec.n++;
  var msg=m==null?"null":typeof m==="string"?"s"+m.length:(m&&m.sigBytes?"word"+m.sigBytes:typeof m);
  var key=k==null?"null":typeof k==="string"?"s"+k.length:(k&&k.sigBytes?"word"+k.sigBytes:typeof k);
  var cfg=c&&typeof c==="object"?Object.keys(c).slice(0,6).join("|"):typeof c;
  if(rec.n<=3 && m && m.words){
    rec.msg=msg; rec.key=key; rec.cfg=cfg; rec.head=head(m);
    var brace=findBrace(m);
    var gzipAt=-1; var n=m.sigBytes||0; for(var gi=0;gi+1<n;gi++){if(byteAt(m,gi)===31&&byteAt(m,gi+1)===139){gzipAt=gi;break;}}
    var head16=[]; for(var hi=0;hi<16&&hi<n;hi++) head16.push(byteAt(m,hi));
    rec.scan="gzip"+gzipAt+" worker"+((globalThis.__workerMsgs)||0)+" words"+m.words.length+" w0"+(m.words[0]>>>0)+" w1"+(m.words[1]>>>0)+" head16 "+head16.join(".")+" n"+n;
    rec.calm=repackBytes(m)+" "+calmMessage(m)+" post "+head(m);
  }
  var out=encrypt.apply(this,arguments);
  if(rec.n<=3){
    rec.chead=out&&out.ciphertext?head(out.ciphertext):"none";
    if(typeof globalThis.__keyClass==="function"){
      try{rec.keyClass=globalThis.__keyClass(k,c,out);}catch(err){rec.keyClass="err";}
    }
  }
  return out;
};
globalThis.__AES=a;
})(n.AES),n.AES)}()
