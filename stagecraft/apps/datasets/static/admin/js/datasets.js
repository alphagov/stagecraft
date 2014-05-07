
(function( jQuery ) {

  var CHARS = "abcdefghjkmnpqrstuvwxyz23456789";

  function generateRandomString(length) {
    var output = "";
    while (output.length < length) {
      output += CHARS[Math.floor(Math.random() * CHARS.length)];
    }
    return output;
  }

  function addGenerateTokenLink() {
    var token_field = jQuery("#id_bearer_token"),
        anchor = jQuery('<a href="#">generate token</a>');

    anchor.click(function(event) {
      event.preventDefault();
      var answer = true;
      if (token_field.val().length > 0) {
        answer = confirm("The bearer token field is not empty, are you sure you want to regenerate it?");
      }
      if (answer) {
        token_field.val(generateRandomString(64));
      }
    });
    token_field.after(anchor);
  }

  jQuery(addGenerateTokenLink);

})( django.jQuery );
