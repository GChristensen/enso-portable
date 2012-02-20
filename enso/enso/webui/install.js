var enso = {
  init: function() {
    var as = document.getElementsByTagName("a");
    for (var i=0; i<as.length; i++) {
      var main = as[i];
      var rel = main.getAttribute("rel");
      if (!rel || rel != "ensocommand") continue;
      var form = document.createElement("form");
      form.action = "http://localhost:31750/";
      form.method = "POST";
      form.style.display = "inline";
      var inp = document.createElement("input");
      inp.type = "hidden"; inp.name = "url"; inp.value = main.href;
      var sub = document.createElement("input");
      sub.type = "submit"; sub.value = "Install";
      var ref = document.createElement("input");
      ref.type = "hidden"; ref.name = "ref"; ref.value = location.href;
      form.appendChild(inp); form.appendChild(sub); form.appendChild(ref); 
      if (main.nextSibling) {
        main.parentNode.insertBefore(form, main.nextSibling);
      } else {
        main.parentNode.appendChild(form);
      }
    }
  }
};
(function(i) {var u =navigator.userAgent;var e=/*@cc_on!@*/false; var st =
setTimeout;if(/webkit/i.test(u)){st(function(){var dr=document.readyState;
if(dr=="loaded"||dr=="complete"){i()}else{st(arguments.callee,10);}},10);}
else if((/mozilla/i.test(u)&&!/(compati)/.test(u)) || (/opera/i.test(u))){
document.addEventListener("DOMContentLoaded",i,false); } else if(e){     (
function(){var t=document.createElement('doc:rdy');try{t.doScroll('left');
i();t=null;}catch(e){st(arguments.callee,0);}})();}else{window.onload=i;}})(enso.init);

