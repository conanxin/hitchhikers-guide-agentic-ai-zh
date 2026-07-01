
(()=>{const p=document.getElementById("reading-progress"),b=document.getElementById("back-top");function u(){if(!p)return;const d=document.documentElement,m=d.scrollHeight-innerHeight,c=m>0?scrollY/m*100:0;p.style.width=`${Math.max(0,Math.min(100,c))}%`;b?.classList.toggle("visible",scrollY>700)}addEventListener("scroll",u,{passive:true});addEventListener("resize",u);u()})();
