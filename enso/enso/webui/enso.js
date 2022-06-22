function makeEnsoAuthHeader() {
    const headers = {};
    const token = document.querySelector("meta[name='enso-token']").content;
    headers["Authorization"] = "Basic " + btoa("default:" + token);
    return headers;
}

function ensoGet(url, callback) {
    $.ajax({
        url,
        headers: makeEnsoAuthHeader(),
        success: callback
    })
}

function ensoGetJSON(url, callback) {
    $.ajax({
        url,
        headers: makeEnsoAuthHeader(),
        dataType: "json",
        success: callback
    })
}

function ensoPost(url, params) {
    $.ajax({
        url,
        method: "POST",
        data: params,
        headers: makeEnsoAuthHeader(),
    })
}