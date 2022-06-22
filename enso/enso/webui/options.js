
$(onDocumentLoad);

function onDocumentLoad() {

    ensoGet("/api/enso/version", function (data) {
        $("#enso-version").text(data);
    });
    ensoGet("/api/python/version", function (data) {
        $("#python-version").text(data);
    });

    ensoGetJSON("/api/enso/color_themes", function (data) {

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
          ensoGet("/api/enso/set/config/COLOR_THEME/" + theme);
        });
    });

    ensoGet("/api/retreat/installed", function (data) {
        if (data) {
            $("#retreat-settings").css("visibility", "visible");

            ensoGet("/api/enso/get/config/RETREAT_DISABLE", function (data) {
                if (data !== "True")
                    $("#retreat-enable").prop("checked", true);
                else
                    $("#retreat-show-icon").prop("disabled", true);
            });

            $("#retreat-enable").change(function () {
                var retreat_disable = !$("#retreat-enable").prop("checked");
                ensoGet("/api/enso/set/config/RETREAT_DISABLE/" + (retreat_disable? "True": "False"));
                $("#retreat-show-icon").prop("disabled", retreat_disable);
            });

            ensoGet("/api/enso/get/config/RETREAT_SHOW_ICON", function (data) {
                $("#retreat-show-icon").prop("checked", data !== "False");
            });

            $("#retreat-show-icon").change(function () {
                ensoGet("/api/enso/set/config/RETREAT_SHOW_ICON/"
                    + ($("#retreat-show-icon").prop("checked")? "True": "False"));
            });

            // $("#retreat-show-options").click(function(event) {
            //     event.preventDefault();
            //     ensoGet("/api/retreat/show_options");
            // });
        }
    });

    ensoGet("/api/enso/get/config_dir", function (data) {
        $("#enso-user-config").val(data);
    });

    $("#open-in-explorer").click(function(event) {
        event.preventDefault();
        ensoGet("/api/enso/open/config_dir");
    });


    editor = ace.edit("ensorc-box");
    editor.setTheme("ace/theme/monokai");
    editor.getSession().setMode("ace/mode/python");
    editor.setPrintMarginColumn(120);
    editor.renderer.setShowGutter(false);


    var ensorc_help = ``;

    $.ajax({
        url: '/api/enso/get/ensorc',
        type: 'GET',
        headers: makeEnsoAuthHeader(),
        success: function(data) {
            if (data) {
                data = data.trim();
                if (data)
                    editor.getSession().setValue(data);
                // else
                //     editor.getSession().setValue(ensorc_help);
            }
            // else
            //     editor.getSession().setValue(ensorc_help);
        },
        error: function(data) {
            editor.getSession().setValue(ensorc_help)
        }
    });

    // editor.on("focus", function (event) {
    //     if (editor.getSession().getValue() === ensorc_help)
    //         editor.getSession().setValue("");
    // });

    editor.on("blur", function (event) {
        var ensorc = editor.getSession().getValue();
        //if (ensorc !== ensorc_help) {
            $.ajax({
                url: '/api/enso/set/ensorc',
                headers: makeEnsoAuthHeader(),
                type: 'POST',
                data: {ensorc: ensorc}});
            //if (!ensorc)
            //    editor.getSession().setValue(ensorc_help);
        //}
    });
}