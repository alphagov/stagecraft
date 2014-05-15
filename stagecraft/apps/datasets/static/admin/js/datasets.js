(function( $ ) {

    function generate_data_set_name(data_group_name, data_type_name, $data_set_name_selector) {
      var data_set_name = [data_group_name, data_type_name].join('_').replace('-','_','g');

      if(!$data_set_name_selector.length){
        $('<p id=id_data_set>'+data_set_name+'</p>').insertAfter('.field-name label');
      }
      $data_set_name_selector.html(data_set_name);
    }

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

  $(function() {

    $("#id_data_group, #id_data_type").on('change', function(){
        generate_data_set_name(
          $("#id_data_group").find("option:selected").text(),
          $("#id_data_type").find("option:selected").text(),
          $("#id_data_set")
        );
      }
    );
  });

})( django.jQuery );
