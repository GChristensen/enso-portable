import{_ as r}from"./AppHeader.vue_vue_type_style_index_0_lang-B41ULFtW.js";import{_ as i}from"./StaticDoc.vue_vue_type_script_setup_true_lang-DnAe-d6T.js";import{g as o}from"./enso-DTex1_vx.js";import{d as t,o as l,c as d,a as s,b as e,t as c,A as h,u as p,j as u,k as g,_ as m}from"./index-BfbyZTJC.js";const f="/images/logo.png",b="/images/enso-16.png",v="/icons/github.ico",y=`<div>\r
    <h3>v1.4 <span class="change-date">July 18, 2026</span></h3>\r
    <ul class="change-info">\r
        <li>Added voice recognition. Commands can be spoken instead of typed, prefixed by a\r
            keyword, e.g.: <em>&ldquo;computer open notepad&rdquo;</em>. Each command is enabled for\r
            voice individually on the <a href="/commands">Your Commands</a> page, where it\r
            can also be hidden from the quasimode (voice-only) or set to ask for a spoken\r
            <em>yes</em> before it runs. Voice recognition can be suspended by a voice command or from the tray\r
            menu, and stops by itself while the workstation is locked. See the\r
            <a href="/tutorial#voice-recognition">tutorial</a> for details.</li>\r
        <li>Experimental Linux port, supporting X11 sessions and Wayland on KDE Plasma. See\r
            README.linux.md.</li>\r
        <li>Experimental macOS port, with the same feature set as the Linux port. See\r
            README.macos.md.</li>\r
    </ul>\r
\r
    <h3>v1.3 <span class="change-date">October 7, 2025</span></h3>\r
    <ul class="change-info">\r
        <li>Migrated to Python 3.14.</li>\r
        <li>Enso user 'lib' directory may be automatically imported as a module before Enso initialization. See help for more details.</li>\r
    </ul>\r
\r
    <h3>v1.2 <span class="change-date">October 4, 2023</span></h3>\r
    <ul class="change-info">\r
        <li>Migrated to Python 3.13.</li>\r
        <li>Added some Windows utilities such as regedit, msconfig, and event viewer to the "open" command.</li>\r
        <li>Added boolean configuration variable QUASIMODE_BYPASS_TO_RDP to bypass quasimode when an RDP session window is at the focus.</li>\r
        <li>Added string UI_FONT configuration variable to configure UI font.</li>.\r
    </ul>\r
\r
    <h3>v1.1 <span class="change-date">October 4, 2023</span></h3>\r
    <ul class="change-info">\r
        <li>Migrated to Python 3.12.</li>\r
    </ul>\r
\r
    <h3>v1.0 <span class="change-date">October 24, 2022</span></h3>\r
    <ul class="change-info">\r
        <li>Migrated to Python 3.11.</li>\r
    </ul>\r
\r
    <h3>v0.9 <span class="change-date">December 24, 2021</span></h3>\r
    <ul class="change-info">\r
        <li>Added support of internationalized input.</li>\r
    </ul>\r
\r
    <h3>v0.8 <span class="change-date">October 6, 2021</span></h3>\r
    <ul class="change-info">\r
        <li>Migrated to Python 3.10.</li>\r
    </ul>\r
\r
    <h3>v0.7 <span class="change-date">June 22, 2021</span></h3>\r
    <ul class="change-info">\r
        <li>Enso now can properly work with elevated processes when digitally signed. See the GitHub page for more details.</li>\r
        <li>Migrated to x86_64 platform.</li>\r
    </ul>\r
\r
    <h3>v0.6 <span class="change-date">October 7, 2020</span></h3>\r
    <ul class="change-info">\r
        <li>Migrated to Python 3.9.</li>\r
    </ul>\r
\r
    <h3>v0.5 <span class="change-date">October 15, 2019</span></h3>\r
    <ul class="change-info">\r
        <li>Migrated to Python 3.8.</li>\r
        <li>Updated Cairo graphics library to the recent version (1.16.0).</li>\r
        <li>Dropped support of "~/.ensocommands" file.</li>\r
    </ul>\r
\r
    <h3>v0.4 <span class="change-date">March 3, 2019</span></h3>\r
    <ul class="change-info">\r
        <li>Added UWP application support.</li>\r
    </ul>\r
\r
    <h3>v0.3 <span class="change-date">October 9, 2018</span></h3>\r
    <ul class="change-info">\r
        <li>Added the <b>Enso Retreat</b> module.</li>\r
        <li>Added installer.</li>\r
        <li>Added the <b>Tasks</b> feature.</li>\r
        <li>Added Ubiquity-styled settings pages.</li>\r
        <li>Added ability to disable commands.</li>\r
    </ul>\r
\r
    <h3>v0.2 <span class="change-date">September 28, 2018</span></h3>\r
    <ul class="change-info">\r
        <li>Migrated to Python 3.7.</li>\r
        <li>Added new commands: <b>enso install</b>, <b>mpc</b>.</li>\r
        <li>Added mediaprobes.</li>\r
    </ul>\r
\r
    <h3>v0.1 <span class="change-date">September 6, 2018</span></h3>\r
    <ul class="change-info">\r
        <li>Added color theme support.</li>\r
    </ul>\r
\r
    <h3>v0.0.3 <span class="change-date">July 15, 2015</span></h3>\r
    <ul class="change-info">\r
        <li>Added the <b>capslock toggle</b> command.</li>\r
    </ul>\r
\r
    <h3>v0.0.2 <span class="change-date">May 28, 2015</span></h3>\r
    <ul class="change-info">\r
        <li>Migrated to Python 2.7.</li>\r
    </ul>\r
\r
    <h3>v0.0.1 <span class="change-date">February 20, 2012</span></h3>\r
    <ul class="change-info">\r
        <li>Initial release.</li>\r
    </ul>\r
</div>
`,_={id:"about-container"},A={id:"about-version-panel"},w={id:"about-version"},k=t({__name:"AboutView",setup(E){const a=u("");return l(async()=>{a.value=await o()}),(M,n)=>(g(),d("div",_,[s(r,{title:"About"}),e("div",A,[n[0]||(n[0]=e("img",{id:"enso-logo",src:f,height:"145",alt:"Enso"},null,-1)),n[1]||(n[1]=e("h1",null,"Enso Launcher (Open-Source)",-1)),e("h2",w,"Version: "+c(a.value),1),n[2]||(n[2]=h('<div class="about-links" data-v-5df698ae><img class="favicon" src="'+b+'" alt="" data-v-5df698ae><a class="about-link" href="https://gchristensen.github.io/enso-portable/" target="_blank" rel="noopener" data-v-5df698ae>Homepage</a> | <img class="favicon" src="'+v+'" alt="" data-v-5df698ae><a class="about-link" href="https://github.com/GChristensen/enso-portable/" target="_blank" rel="noopener" data-v-5df698ae>GitHub</a></div>',1))]),n[3]||(n[3]=e("div",{id:"about-changes-header"},[e("h2",null,"Changes")],-1)),s(i,{id:"about-changes",html:p(y)},null,8,["html"])]))}}),D=m(k,[["__scopeId","data-v-5df698ae"]]);export{D as default};
