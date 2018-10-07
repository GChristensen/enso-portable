function saveTasks(callback) {
    var customscripts = editor.getSession().getValue();
    try {
        // save
        $.post("/api/enso/write_tasks", {code: customscripts});

        // download link
        var a = document.getElementById("download");
        var file = new Blob([customscripts], {type: "application/python"});
        a.href = URL.createObjectURL(file);
        a.download = "tasks.py";
    }
    catch (e) {
        console.error(e);
    }

    if (callback && typeof callback === "function")
        callback();
}

$(() => {

    var tasks_help = `# Tasks is a block of code executed in a separate thread on Enso start.
# You may use your favorite scheduling library to schedule tasks here.`;

    editor = ace.edit("code");
    editor.setTheme("ace/theme/monokai");
    editor.getSession().setMode("ace/mode/python");
    editor.setPrintMarginColumn(120);

    $(window).on('resize', e => {
        editor.container.style.height = $(window).innerHeight() - $("#header").height() - $("#footer").height() - 20;
        editor.resize();
    });
    $(window).resize();

    function editTasks() {
        $.ajax({
            url: "/api/enso/read_tasks",
            type: 'GET',
            success: function(data) {
                if (data) {
                    data = data.trim();
                    if (data)
                        return editor.setValue(data, -1);
                    else
                        editor.getSession().setValue(tasks_help);
                }
                else
                    editor.getSession().setValue(tasks_help);
            },
            error: function(data) {
                editor.getSession().setValue(tasks_help)
            }
        });
    }

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

    editTasks();

    editor.on("focus", function (event) {
        if (editor.getSession().getValue() === tasks_help)
            editor.getSession().setValue("");
    });

    editor.on("blur", function (event) {
        var tasks = editor.getSession().getValue();
        if (tasks !== tasks_help) {
            saveTasks();
            if (!tasks)
                editor.getSession().setValue(tasks_help);
        }
    });

    // editor.on("blur", saveTasks);
    //
    // let timeout;
    // function delayedSave() {
    //     if (timeout)
    //         clearTimeout(timeout);
    //     timeout = setTimeout(function () {
    //         saveTasks();
    //         timeout = null;
    //     }, 1000);
    // }
    //
    // editor.on("change", delayedSave);

    //editor.focus();
});