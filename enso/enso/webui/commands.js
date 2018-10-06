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

    var checkBoxCell = $('<td><input type="checkbox"/></td>');
    (checkBoxCell.find("input")
        .val(cmd.id)
        .bind("change", (e) => {
            cmd.disabled = !e.target.checked;
            if (cmd.disabled)
                $.get("/api/enso/commands/disable/" + name);
            else
                $.get("/api/enso/commands/enable/" + name);
        })
        [cmd.disabled ? "removeAttr" : "attr"]("checked", "checked"));

    var cmdElement = jQuery(
        '<td class="command">'
        //'<img class="favicon" src="'
        //+ escapeHtml((!("icon" in cmd) || cmd["icon"] === "http://example.com/favicon.png")? "/res/icons/icon-24.png": cmd.icon) + '"/>' +
        + ('<a class="id" name="' + escapeHtml(cmd.id) + '"/>' +
            '<span class="name">' + escapeHtml(name) + '</span>') +
        '<span class="description"></span>' +
        '<div class="help"></div>' +
        '</td>');

    if (className) {
        checkBoxCell.addClass(className);
        cmdElement.addClass(className);
    }

    for (let key of ["description", "help"]) if (key in cmd) {
        let node = cmdElement[0].getElementsByClassName(key)[0];
        try { node.innerHTML = cmd[key] }
        catch (e) {
            let msg = 'XML error in "' + key + '" of [ ' + cmd.name + ' ]';
            console.error(msg);
        }
    }

    return row.append(checkBoxCell, cmdElement);
}

function insertNamespace(namespace, subtext, commands, table) {
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
    else
        aRow.append("<td class=\"topcell command\">&nbsp</td><td class=\"topcell command\">&nbsp</td>");
}

function buildTable() {
    let table = jQuery("#commands-and-feeds-table");

    $.getJSON("/api/enso/get/commands", function (data) {

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
                + '" target="_blank">Open in editor</a>', commands.filter(c => c.category === cat).sort(), table);
    });
}

jQuery(function onReady() {
    setupHelp("#show-hide-help", "#cmdlist-help-div");
    buildTable();
});
