$(function () {
  $("#ctn_result").hide();

  $("#savetestcase").click(function () {
    let interfaces = $(".slider")
      .get()
      .map((elem) => ({
        interface_id: elem.id,
        bw: elem.value,
      }));
    let data_request={};
    data_request.interfaces = interfaces;
    data_request.test_name = $("#test_name").val()
    data_request.test_id = $("#test_id").val()
    $.ajax({
      url: "/saveTest",
      data: JSON.stringify(data_request),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      type: "POST",
      success: function (response) {
        $("#resut_msg").html(response.message);
        $("#ctn_result").show();
        setInterval(function(){ $("#ctn_result").hide();}, 1000);

      },
      error: function (error) {
        console.log(error);
      },
    });
  });

});
