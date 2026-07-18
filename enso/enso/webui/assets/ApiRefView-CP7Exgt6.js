import{_ as r}from"./AppHeader.vue_vue_type_style_index_0_lang-B41ULFtW.js";import{_ as t}from"./StaticDoc.vue_vue_type_script_setup_true_lang-DnAe-d6T.js";import{d as n,c as a,a as e,u as o,F as i,k as s}from"./index-BfbyZTJC.js";const c=`<div class="doc-body">\r
    <h1 style="margin-top: 25px"><a id="user-content-enso-api-reference" class="anchor" aria-hidden="true" href="#enso-api-reference"></a>Enso API Reference</h1>\r
    <h2>ensoapi object methods</h2>\r
    <h3><a class="anchor" aria-hidden="true" href="#"></a>display_message(msg, caption=None)</h3>\r
    <blockquote>\r
        <p>Displays the given message, with an optional caption.  Both\r
            parameters should be Unicode strings.</p>\r
    </blockquote>\r
\r
    <h3><a class="anchor" aria-hidden="true" href="#"></a>get_selection()</h3>\r
    <blockquote>\r
        <p>Retrieves the current selection and returns it as a\r
            selection dictionary (see the tutorial for more information).</p>\r
    </blockquote>\r
\r
    <h3><a class="anchor" aria-hidden="true" href="#"></a>set_selection(seldict)</h3>\r
    <blockquote>\r
        <p> Sets the current selection to the contents of the given\r
            selection dictionary.<br>\r
\r
            Alternatively, if a string is provided instead of a\r
            dictionary, the current selection is set to the Unicode\r
            contents of the string.</p>\r
    </blockquote>\r
\r
    <h3><a class="anchor" aria-hidden="true" href="#"></a>get_enso_user_folder()</h3>\r
    <blockquote>\r
        <p>Returns the location of the Enso user configuration folder.</p>\r
    </blockquote>\r
\r
    <h2>mediaprobe module functions</h2>\r
    <h3><a class="anchor" aria-hidden="true" href="#"></a>dictionary_probe(category, dictionary, player="", all="", findfirst=False)</h3>\r
    <blockquote>\r
        <p>Sends values found in the dictionary to the <b>player</b>. Obtains command arguments from the dictionary entries.<br><br>\r
            The <b>category</b> parameter specifies the name of the generated command argument.<br>\r
            If <b>findfirst</b> is true and the dictionary item value is a directory path, the first file found\r
            in the directory is sent into the player instead of the item.<br>\r
            If the <b>player</b> argument is an empty string, the default shell application is used.<br>\r
            The 'all' command argument value is substituted by the <b>all</b> function parameter.</p>\r
    </blockquote>\r
\r
    <h3><a class="anchor" aria-hidden="true" href="#"></a>directory_probe(category, directory, player="", additional=None)</h3>\r
    <blockquote>\r
        <p>Sends directory entries found in the <b>directory</b> to the <b>player</b>. Obtains command arguments from the directory entries.<br><br>\r
            The <b>category</b> parameter specifies the name of the generated command argument.<br>\r
            The <b>additional</b> function parameter allows the creation of additional command argument values (from a supplied dictionary), not found in the <b>directory</b>.</p>\r
    </blockquote>\r
\r
    <h3><a class="anchor" aria-hidden="true" href="#"></a>findfirst_probe(category, dictionary, player="")</h3>\r
    <blockquote>\r
        <p>Uses the default shell program to open the first <i>file</i> in the <b>directory</b>; uses the <b>player</b> if given. Obtains command arguments from the directory entries.<br><br>\r
            The <b>category</b> parameter sets the name of the generated command argument.<br></p>\r
    </blockquote>\r
</div>
`,f=n({__name:"ApiRefView",setup(h){return(d,l)=>(s(),a(i,null,[e(r,{title:"API"}),e(t,{html:o(c)},null,8,["html"])],64))}});export{f as default};
