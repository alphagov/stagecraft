(function( $ ) {

  function generateRandomString(length) {
    var CHARS = "abcdefghjkmnpqrstuvwxyz23456789",
        output = "";
    while (output.length < length) {
      output += CHARS[Math.floor(Math.random() * CHARS.length)];
    }
    return output;
  }

  function addGenerateTokenLink() {
    var $token_field = $("#id_bearer_token"),
  $anchor = $('<a href="#">generate token</a>');

    $token_field.after($anchor);

    $anchor.on("click", function(event){
      event.preventDefault();

      var answer = true;
      if ($token_field.val().length > 0) {
        answer = confirm("The bearer token field is not empty, are you sure you want to regenerate it?");
      }
      if (answer) {
  $token_field.val(generateRandomString(64));
      }

    });

  }

  $(addGenerateTokenLink);

})( django.jQuery );
