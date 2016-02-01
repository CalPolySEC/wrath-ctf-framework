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
});
