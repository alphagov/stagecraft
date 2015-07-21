(function($) {
    $(function () {
        var $typeSelect = $('#id_type');
        var $dataSourceSelect = $('#id_data_source');
        var $options = $dataSourceSelect.find('option:not(:first)');
        var intitialSelectedValue = $dataSourceSelect.find('[selected]').val();
        if (intitialSelectedValue)
            populateFields(intitialSelectedValue);

        $typeSelect.change(function (){
          var selectedValue = $(this).val();
          populateFields(selectedValue);
        });

        function populateFields (selectedValue){
          if (selectedValue === ''){
            $options.remove();
            $dataSourceSelect.append($options);
          }
          else {
            var providerId = $('[value=' + selectedValue + ']').data('id');
            $options.remove();

            $.each($options, function(){
              if ($(this).data('id') == providerId){
                $dataSourceSelect.append($(this));
              }
            });

          }
        }

    });

})(django.jQuery);
