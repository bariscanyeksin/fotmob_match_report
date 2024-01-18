function myChangeFunction() {
    var e = document.getElementById("firstteam");
    var text = e.options[e.selectedIndex].text;
    var value = e.value;

    document.getElementById("firstteamName").value = text;
    document.getElementById("firstteamId").value = value;
}

window.enabled = false;

function showPicture() {
    enabled = !enabled;

    if (enabled) {
        var sourceOfPicture = "https://i.ibb.co/QX5jScZ/matchid.png";
        var img = document.getElementById('macid_img')
        img.src = sourceOfPicture.replace('90x90', '225x225');
        img.style.display = "inline";
    }

    else {
        var sourceOfPicture = "https://i.ibb.co/QX5jScZ/matchid.png";
        var img = document.getElementById('macid_img')
        img.src = sourceOfPicture.replace('90x90', '225x225');
        img.style.display = "none";
    }
  }

function myFunction() {
    var x = document.getElementById("mySelect").value;
    document.getElementById("macId").value = x;
  }