
lastNamespace = localStorage.getItem("lastNamespace");

scriptNamespace =  window.location.search
        ? decodeURI(window.location.search.substring(1))
        : (lastNamespace? lastNamespace: "user");

function insertExampleStub() {
    var stubs = {
        'insertsimplecommandstub':
`def cmd_my_command(ensoapi):
    """My command description"""
    ensoapi.display_message("Hello world!")`,

  'insertvarargsstub':
`def cmd_my_command(ensoapi, argument):
    """My command description"""
    ensoapi.display_message(argument)`,

        'insertboundargsstub':
`def cmd_my_command(ensoapi, argument):
    """My command description"""
    ensoapi.display_message(argument)

cmd_my_command.valid_args = ["arg1", "arg2"]`
    };

    var stub = stubs[this.id];
    editor.session.insert(editor.getCursorPosition(), stub);

    editor.focus();
    return false;
}

function saveScripts(callback) {
    var customscripts = editor.getSession().getValue();
    try {
        // save
        $.post("/api/enso/commands/write_category/" + scriptNamespace, {code: customscripts});

        // download link
        var a = document.getElementById("download");
        var file = new Blob([customscripts], {type: "application/python"});
        a.href = URL.createObjectURL(file);
        a.download = scriptNamespace + ".py";
    }
    catch (e) {
        console.error(e);
    }

    if (callback && typeof callback === "function")
        callback();
}

$(() => {

    editor = ace.edit("code");
    editor.setTheme("ace/theme/monokai");
    editor.getSession().setMode("ace/mode/python");
    editor.setPrintMarginColumn(120);

    $(window).on('resize', e => {
       editor.container.style.height = $(window).innerHeight() - $("#header").height() - $("#footer").height() - 20;
       editor.resize();
    });
    $(window).resize();

    function editNamespaceScripts(namespace) {
        $.get("/api/enso/commands/read_category/" + namespace, function (data) {
            if (data)
                return editor.setValue(data, -1);
            else
                return editor.setValue("");
        });
    }

    $("#script-namespaces").change(() => {


        saveScripts(() => {
            scriptNamespace = $("#script-namespaces").val();
            localStorage.setItem("lastNamespace", scriptNamespace);
            editNamespaceScripts(scriptNamespace);
        });
    });

    $("#upload").click((e) => {
        $("#file-picker").click();
    });

    $("#file-picker").change((e) => {
       if (e.target.files.length > 0) {
           let reader = new FileReader();
           reader.onload = function(e) {
               editor.getSession().setValue(e.target.result);
           };
           reader.readAsText(e.target.files[0]);
       }
    });

    $("#create-namespace").click(() => {
        let name = prompt("Create category: ");
        if (name) {
            ADD_NAME: {
                let opts = $("#script-namespaces option");

                for (opt of opts) {
                    if (opt.value === name) {
                        scriptNamespace = name;
                        $("#script-namespaces").val(name);
                        editNamespaceScripts(scriptNamespace)
                        break ADD_NAME
                    }
                }

                scriptNamespace = name;
                editor.getSession().setValue("");
                $("#script-namespaces").append($("<option></option>")
                    .attr("value", name)
                    .text(name))
                    .val(name);
            }
        }
    });

    $("#delete-namespace").click(() => {
        if (scriptNamespace !== "user")
            if (confirm("Do you really want to delete \"" + scriptNamespace + "\"?")) {
                $.get("/api/enso/commands/delete_category/" + scriptNamespace, function (data) {
                    $('option:selected', $("#script-namespaces")).remove();
                    scriptNamespace = $("#script-namespaces").val();
                    editNamespaceScripts(scriptNamespace);
                });
            }
    });

    $("#expand-editor").click(() => {
        if ($("#expand-editor img").prop("src").endsWith("/images/collapse.png")) {
            $("#panel").css("width", "870px");
            $("body").css("margin", "auto");
            $("body").css("max-width", "900px");
            $("#toolbar").css("padding-right", "30px");
            $(".head, #nav-container, #head-br").show();
            $("#expand-editor img").prop("src", "/images/expand.png");
        }
        else {
            $(".head, #nav-container, #head-br").hide();
            $("#panel").css("width", "100%");
            $("body").css("margin", "0");
            $("body").css("max-width", "100%");
            $("#toolbar").css("padding-right", "5px");
            $("#expand-editor img").prop("src", "/images/collapse.png");
        }
        window.dispatchEvent(new Event('resize'));
        editor.focus();
    });

    $("#insertsimplecommandstub").click(insertExampleStub);
    $("#insertvarargsstub").click(insertExampleStub);
    $("#insertboundargsstub").click(insertExampleStub);

    // load scrtips
    $.getJSON("/api/enso/get/user_command_categories", function (data) {
        for (let n of data)
            if (n !== "user")
                $("#script-namespaces").append($("<option></option>")
                    .attr("value", n)
                    .text(n));
        $("#script-namespaces").val(scriptNamespace);

        editNamespaceScripts(scriptNamespace);
    });

    editor.on("blur", saveScripts);

    let timeout;
    function delayedSave() {
        if (timeout)
            clearTimeout(timeout);
        timeout = setTimeout(function () {
            saveScripts();
            timeout = null;
        }, 1000);
    }

    editor.on("change", delayedSave);

    editor.focus();
});