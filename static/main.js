function setCookie(key, val) {
  var d = new Date();
  d.setTime(d.getTime() + 5 * 60 * 1000);
  document.cookie = key + '=' + val + '; path=/; expires=' + d.toGMTString()
    + ';';
};

$(function() {
  var togglePasword = function() {
    var shown = true;
    return function() {
      $('.password').each(function() {
        var password = $(this).data('password');
        if (shown) {
          $(this).html('*'.repeat(password.length));
        } else {
          $(this).text(password);
        }
      });
      shown = !shown;
    };
  }();
  togglePasword();

  $('#show-password').click(function() {
    if ($(this).text() == 'Show') {
      $(this).text('Hide');
    } else {
      $(this).text('Show');
    }
    togglePasword();
  });

  $('.level').tooltip();

  /* Auto-update */
  (function() {
    var timer = null;

    var setUpdate = function() {
      return setTimeout(function () {
        location.reload();
      }, 30000);
    }

    var updateReloadTimerState = function() {
      if ($('#autoupdate').is(':checked')) {
        setCookie('autoupdate', '1');
        timer = setUpdate();
      } else {
        if (timer !== null) {
          clearTimeout(timer);
          timer = null;
        }
        setCookie('autoupdate', '0');
      }
    };
    $('#autoupdate').change(updateReloadTimerState);
    updateReloadTimerState();
  })();

  console.log('Hello, friend.');
});
