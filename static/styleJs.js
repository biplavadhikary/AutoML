var currentTab = 0;
showTab(currentTab);

function showTab(n) {
  var x = document.getElementsByClassName("tab");
  x[n].style.display = "block";
  if (n == 0) {
    prev = document.getElementsByClassName("previous")[0];
    prev.classList.remove('previous');
    prev.classList.add('invalid');
    //prev.style.display = "none";
  } else {
    prev = document.getElementsByClassName("invalid")[0];
    prev.classList.remove('invalid');
    prev.classList.add('previous');
    //prev.style.display = "inline-block";
  }
  if (n == (x.length - 1)) {
    next = document.getElementsByClassName("next")[0];
    next.innerHTML = "<i class='fa fa-paper-plane' aria-hidden='true' style='font-size:24px'></i>"
    next.classList.remove('round');
  } else {
    next = document.getElementsByClassName("next")[0];
    next.innerHTML = "<i class='fas fa-chevron-right' style='font-size:24px'></i>"
    next.classList.add('round');
  }
  
  fixStepIndicator(n)
}

function nextPrev(n) {
  if (currentTab + n < 0 )
    return;

  var x = document.getElementsByClassName("tab");
  // Exit the function if any field in the current tab is invalid:
  if (n == 1&&!validateForm())
    return false;

  var oldTab = currentTab
  currentTab = currentTab + n;

  if (currentTab >= x.length) {
    // The form got submitted
    document.getElementById("dataProp").submit();
    return false;
  }

  x[oldTab].style.display = "none";

  showTab(currentTab);
}

function validateForm() {
  var x, y, i, valid = true;
  x = document.getElementsByClassName("tab");
  y = x[currentTab].getElementsByTagName("input");
  
  for (i = 0; i < y.length; i++) {
    if (y[i].value == "") {
      y[i].className += " invalid";
      valid = false;
    }
  }

  y = x[currentTab].getElementsByTagName("select")
  if(y.length != 0) {
    if(y[0].value == "#")
      valid = false;
  }

  if (valid) {
    document.getElementsByClassName("step")[currentTab].className += " finish";
    
  }
  return valid;
}

function fixStepIndicator(n) {
  var i, x = document.getElementsByClassName("step");
  for (i = 0; i < x.length; i++) {
    x[i].className = x[i].className.replace(" active", "");
  }

  x[n].className += " active";
}

// Part 2 : Dropdown Menu

var x, i, j, selElmnt, a, b, c;
x = document.getElementsByClassName("custom-select");
for (i = 0; i < x.length; i++) {
  selElmnt = x[i].getElementsByTagName("select")[0];
  a = document.createElement("DIV");
  a.setAttribute("class", "select-selected");
  a.innerHTML = selElmnt.options[selElmnt.selectedIndex].innerHTML;
  x[i].appendChild(a);
  b = document.createElement("DIV");
  b.setAttribute("class", "select-items select-hide");
  for (j = 1; j < selElmnt.length; j++) {
    c = document.createElement("DIV");
    c.innerHTML = selElmnt.options[j].innerHTML;
    c.addEventListener("click", function(e) {
        var y, i, k, s, h;
        s = this.parentNode.parentNode.getElementsByTagName("select")[0];
        h = this.parentNode.previousSibling;
        for (i = 0; i < s.length; i++) {
          if (s.options[i].innerHTML == this.innerHTML) {
            s.selectedIndex = i;
            h.innerHTML = this.innerHTML;
            y = this.parentNode.getElementsByClassName("same-as-selected");
            for (k = 0; k < y.length; k++) {
              y[k].removeAttribute("class");
            }
            this.setAttribute("class", "same-as-selected");
            break;
          }
        }
        h.click();
    });
    b.appendChild(c);
  }
  x[i].appendChild(b);
  a.addEventListener("click", function(e) {
    e.stopPropagation();
    closeAllSelect(this);
    this.nextSibling.classList.toggle("select-hide");
    this.classList.toggle("select-arrow-active");
  });
}

function closeAllSelect(elmnt) {
  var x, y, i, arrNo = [];
  x = document.getElementsByClassName("select-items");
  y = document.getElementsByClassName("select-selected");
  for (i = 0; i < y.length; i++) {
    if (elmnt == y[i]) {
      arrNo.push(i)
    } else {
      y[i].classList.remove("select-arrow-active");
    }
  }
  for (i = 0; i < x.length; i++) {
    if (arrNo.indexOf(i)) {
      x[i].classList.add("select-hide");
    }
  }
}

document.addEventListener("click", closeAllSelect);

/* ======================================================
Footer
====================================================== */

$(document).ready(function() {

  $('.footerDrawer .open').on('click', function() {

    $('.footerDrawer .content').slideToggle();

  });

});

/* Button Copy to Clipboard */

function copyToClipboard() {
  var copyText = document.getElementById("token");
  copyText.select();
  copyText.setSelectionRange(0, 99999);
  document.execCommand("copy");
  
  var tooltip = document.getElementById("myTooltip");
  tooltip.innerHTML = "Copied: " + copyText.value;
}

function outFunc() {
  var tooltip = document.getElementById("myTooltip");
  tooltip.innerHTML = "Copy to clipboard";
}