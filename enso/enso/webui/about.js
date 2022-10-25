//$("#about-changes").html(await fetchText("changes.html"));
//$("#about-version").text(`Version: ${chrome.runtime.getManifest().version}`);

$(() => {
    $(".donation-link").on("mouseenter", e => { $("#enso-logo").prop("src", "images/donation_kitty.png"); console.log("aaa")});
    $(".donation-link").on("mouseleave", e => $("#enso-logo").prop("src", "images/logo.png"));

    ensoGet("/api/enso/version", function (data) {
        $("#about-version").text("Version: " + data);
    });

    ensoGet("/changes.html", function (data) {
        $("#about-changes").html(data);
    });
});
