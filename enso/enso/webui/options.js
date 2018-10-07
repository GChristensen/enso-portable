
$(onDocumentLoad);

function onDocumentLoad() {

    $.get("/api/enso/version", function (data) {
        $("#enso-version").text(data);
    });
    $.get("/api/python/version", function (data) {
        $("#python-version").text(data);
    });

    $.getJSON("/api/enso/color_themes", function (data) {

        var $themeSelect = $("#theme-select");

        if ("default" in data.all)
          delete data.all["default"];

        for (let theme in data.all) {
           let $opt = $("<option>", {val: theme, text: theme});
           $opt[0].selected = theme === data.current;
           $themeSelect.append($opt);
        }

        $themeSelect.change(() => {
          let theme = $themeSelect.find(":selected").val();
          $.get("/api/enso/set/config/COLOR_THEME/" + theme);
        });
    });

    $.get("/api/retreat/installed", function (data) {
        if (data) {
            $("#retreat-settings").css("visibility", "visible");

            $.get("/api/enso/get/config/RETREAT_DISABLE", function (data) {
                if (data !== "True")
                    $("#retreat-enable").prop("checked", true);
                else
                    $("#retreat-show-icon").prop("disabled", true);
            });

            $("#retreat-enable").change(function () {
                var retreat_disable = !$("#retreat-enable").prop("checked");
                $.get("/api/enso/set/config/RETREAT_DISABLE/" + (retreat_disable? "True": "False"));
                $("#retreat-show-icon").prop("disabled", retreat_disable);
            });

            $.get("/api/enso/get/config/RETREAT_SHOW_ICON", function (data) {
                $("#retreat-show-icon").prop("checked", data !== "False");
            });

            $("#retreat-show-icon").change(function () {
                $.get("/api/enso/set/config/RETREAT_SHOW_ICON/"
                    + ($("#retreat-show-icon").prop("checked")? "True": "False"));
            });

            // $("#retreat-show-options").click(function(event) {
            //     event.preventDefault();
            //     $.get("/api/retreat/show_options");
            // });
        }
    });

    $.get("/api/enso/get/config_dir", function (data) {
        $("#enso-user-config").val(data);
    });

    $("#open-in-explorer").click(function(event) {
        event.preventDefault();
        $.get("/api/enso/open/config_dir");
    });


    editor = ace.edit("ensorc-box");
    editor.setTheme("ace/theme/monokai");
    editor.getSession().setMode("ace/mode/python");
    editor.setPrintMarginColumn(120);
    editor.renderer.setShowGutter(false);


    var ensorc_help = `# Custom Python code needed to initialize Enso.
# Some commands may ask you to declare variables here.
# You can access variables declared at this block 
# in your own commands through the 'config' module.
# For example, you can obtain the following variable:
MY_VARIABLE = "my value"
# with the following code in your command:
from enso import config
my_value = config.MY_VARIABLE`;

    $.ajax({
        url: '/api/enso/get/ensorc',
        type: 'GET',
        success: function(data) {
            if (data) {
                data = data.trim();
                if (data)
                    editor.getSession().setValue(data);
                else
                    editor.getSession().setValue(ensorc_help);
            }
            else
                editor.getSession().setValue(ensorc_help);
        },
        error: function(data) {
            editor.getSession().setValue(ensorc_help)
        }
    });

    editor.on("focus", function (event) {
        if (editor.getSession().getValue() === ensorc_help)
            editor.getSession().setValue("");
    });

    editor.on("blur", function (event) {
        var ensorc = editor.getSession().getValue();
        if (ensorc !== ensorc_help) {
            $.ajax({
                url: '/api/enso/set/ensorc',
                type: 'POST',
                data: {ensorc: ensorc}});
            if (!ensorc)
                editor.getSession().setValue(ensorc_help);
        }
    });


    // $("#export-settings").mouseover((e) => {
    //     chrome.storage.local.get(undefined, (settings) => {
    //         let exported = {};
    //         Object.assign(exported, settings);
    //         exported.version = CmdUtils.VERSION;
    //
    //         Utils.getCustomScripts(all_scripts => {
    //             exported.customScripts = all_scripts;
    //
    //             var file = new Blob([JSON.stringify(exported, null, 2)], {type: "application/json"});
    //             e.target.href = URL.createObjectURL(file);
    //             e.target.download = "ensouity.json";
    //         });
    //     });
    // });
    //
    // $("#import-settings").click((e) => {
    //     e.preventDefault();
    //     $("#file-picker").click();
    // });
    //
    // $("#file-picker").change((e) => {
    //     if (e.target.files.length > 0) {
    //         let reader = new FileReader();
    //         reader.onload = function(re) {
    //             let imported = JSON.parse(re.target.result);
    //
    //             // versioned operations here
    //
    //             if (imported.version)
    //                 delete imported.version;
    //
    //             let customScripts = imported.customScripts;
    //
    //             if (customScripts !== undefined)
    //                 delete imported.customScripts;
    //
    //             chrome.storage.local.set(imported);
    //
    //             if (customScripts && typeof customScripts === "object") {
    //                 let multipleObjects = [];
    //                 try {
    //                     multipleObjects = Object.values(customScripts).map(scripts =>
    //                         Utils.saveCustomScripts(scripts.namespace, scripts.scripts));
    //                 }
    //                 catch (e) {
    //                     console.error(e);
    //                 }
    //                 Promise.all(multipleObjects).then(() => chrome.runtime.reload());
    //             }
    //             else
    //                 chrome.runtime.reload();
    //         };
    //         reader.readAsText(e.target.files[0]);
    //     }
    // });
}