// Whether the voicecmd library is installed; when false the voice
// checkbox columns are omitted entirely. Set in onReady().
var voiceAvailable = false;

let escapeHtml = function(s) {
    return String(s).replace(escapeHtml.re, escapeHtml.fn)
};
escapeHtml.re = /[&<>\"\']/g;
escapeHtml.fn = function escapeHtml_sub($) {
    switch ($) {
        case "&": return "&amp;";
        case "<": return "&lt;";
        case ">": return "&gt;";
        case '"': return "&quot;";
        case "'": return "&#39;";
    }
};

function setupHelp(clickee, help) {
    var toggler = jQuery(clickee).click(function toggleHelp() {
        jQuery(help)[(this.off ^= 1) ? "slideUp" : "slideDown"]();
        [this.textContent, this.bin] = [this.bin, this.textContent];
    })[0];
    toggler.textContent = "Show help";
    toggler.bin = "Hide help";
    toggler.off = true;
}

function A(url, text, className, attrs) {
    var a = document.createElement("a");
    a.href = url;
    a.textContent = text || url;
    if (className) a.className = className;
    for (let attr in attrs) a.setAttribute(attr, attrs[attr]);
    return a;
}

function fillTableCellForFeed(cell, feed, subtext) {

    if (feed == "other")
        feed = "other commands";

    cell.append(
        A("#", feed, ""),
        "<br/>");
    // cell.append(jQuery('<div class="meta">' +
    //     '<div class="author">' + subtext + '</div>'
    //     + '</div>'))
}

function compareByName(a, b) {
    if (a.name < b.name)
        return -1;
    if (a.name > b.name)
        return 1;
    return 0;
}

function fillTableRowForCmd(row, cmd, className) {
    var {name, names} = cmd;

    var cells = [];

    var checkBoxCell = $('<td class="command-check"><input type="checkbox" title="Enabled" /></td>');
    (checkBoxCell.find("input")
        .val(cmd.id)
        .bind("change", (e) => {
            cmd.disabled = !e.target.checked;
            if (cmd.disabled)
                ensoGet("/api/enso/commands/disable/" + name);
            else
                ensoGet("/api/enso/commands/enable/" + name);
        })
        [cmd.disabled ? "removeAttr" : "attr"]("checked", "checked"));
    cells.push(checkBoxCell);

    // The voice columns are only present when the voicecmd library is
    // installed (see onReady / voiceAvailable).
    if (voiceAvailable) {
        var voiceCheckBoxCell = $('<td class="command-check"><input type="checkbox"  title="Voice Command"/></td>');
        (voiceCheckBoxCell.find("input")
            .val(cmd.id)
            .bind("change", (e) => {
                cmd.voice = e.target.checked;
                if (cmd.voice)
                    ensoGet("/api/enso/commands/voice/enable/" + name);
                else
                    ensoGet("/api/enso/commands/voice/disable/" + name);
            })
            [cmd.voice ? "attr" : "removeAttr"]("checked", "checked"));
        cells.push(voiceCheckBoxCell);

        // Voice-only and confirm both qualify *how* a voice command behaves,
        // so either one implies the command is a voice command at all: turning
        // one on checks the voice box too if it isn't already.
        let dependentCell = function (title, prop, route) {
            let cell = $('<td class="command-check"><input type="checkbox" title="'
                + title + '"/></td>');
            (cell.find("input")
                .val(cmd.id)
                .bind("change", (e) => {
                    cmd[prop] = e.target.checked;
                    if (cmd[prop]) {
                        ensoGet("/api/enso/commands/" + route + "/enable/" + name);
                        if (!cmd.voice) {
                            cmd.voice = true;
                            voiceCheckBoxCell.find("input").prop("checked", true);
                            ensoGet("/api/enso/commands/voice/enable/" + name);
                        }
                    } else {
                        ensoGet("/api/enso/commands/" + route + "/disable/" + name);
                    }
                })
                [cmd[prop] ? "attr" : "removeAttr"]("checked", "checked"));
            return cell;
        };

        cells.push(dependentCell("Voice-Only Command", "voiceOnly", "voice_only"));
        cells.push(dependentCell("Confirm Before Running", "voiceConfirm",
                                 "voice_confirm"));
    }

    var cmdElement = jQuery(
        '<td class="command">'
        //'<img class="favicon" src="'
        //+ escapeHtml((!("icon" in cmd) || cmd["icon"] === "http://example.com/favicon.png")? "/res/icons/icon-24.png": cmd.icon) + '"/>' +
        + ('<a class="id" name="' + escapeHtml(cmd.id) + '"/>' +
            '<span class="name">' + escapeHtml(name) + '</span>') +
        '<span class="description"></span>' +
        '<div class="help"></div>' +
        '</td>');
    cells.push(cmdElement);

    if (className) {
        for (let cell of cells)
            cell.addClass(className);
    }

    for (let key of ["description", "help"]) if (key in cmd) {
        let node = cmdElement[0].getElementsByClassName(key)[0];
        try { node.innerHTML = cmd[key] }
        catch (e) {
            let msg = 'XML error in "' + key + '" of [ ' + cmd.name + ' ]';
            console.error(msg);
        }
    }

    return row.append.apply(row, cells);
}

function insertNamespace(namespace, subtext, commands, table) {
    commands = commands.sort(compareByName);

    aRow = jQuery("<tr></tr>");
    feedElement = jQuery('<td class="topcell command-feed" ' + 'rowspan="' + commands.length + '"></td>');
    fillTableCellForFeed(feedElement, namespace, subtext);
    aRow.append(feedElement);

    if (commands.length > 0)
        fillTableRowForCmd(aRow, commands.shift(), "topcell command");

    table.append(aRow);

    if (commands.length > 0) {
        commands.forEach(c => {
            let aRow = jQuery("<tr></tr>");
            fillTableRowForCmd(aRow, c, "command");
            table.append(aRow);
        });
    }
    else {
        // One empty cell per column fillTableRowForCmd would have produced:
        // enable (+ voice, voice-only, confirm when available) + command.
        let emptyCell = "<td class=\"topcell command\">&nbsp</td>";
        aRow.append(emptyCell.repeat(2 + (voiceAvailable ? 3 : 0)));
    }
}

function buildTable() {
    let table = jQuery("#commands-and-feeds-table");

    ensoGetJSON("/api/enso/get/commands", function (data) {

        let commands = data;
        let commandCount = data.length;

        jQuery("#num-commands").text(commandCount);

        let categories = {};
        for (cmd of commands) {
            let category = cmd.category;
            if (!categories[category])
                categories[category] = 1;
            else
                categories[category] += 1;
        }

        categories = Object.keys(categories).sort();

        jQuery("#num-cats").text(categories.length);

        for (let cat of categories)
            insertNamespace(cat, '<a href="edit.html?' + encodeURI(cat)
                + '" target="_blank">Open in editor</a>', commands.filter(c => c.category === cat), table);
    });
}

jQuery(function onReady() {
    setupHelp("#show-hide-help", "#cmdlist-help-div");

    // Discover whether the voice checkbox columns should be shown, then
    // build the table. Uses $.ajax's "complete" so the table is always
    // built even if the availability probe fails (defaulting to hidden).
    $.ajax({
        url: "/api/enso/voice/available",
        headers: makeEnsoAuthHeader(),
        dataType: "json",
        success: function (data) { voiceAvailable = (data === true); },
        complete: function () {
            if (!voiceAvailable)
                jQuery(".voice-header").remove();
            buildTable();
        }
    });
});
