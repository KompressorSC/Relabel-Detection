function moment() {
    var date = new Date();
    var year = date.getFullYear();
    var month = date.getMonth() + 1;
    var day = date.getDate();
    var hour = date.getHours();
    var minute = date.getMinutes();
    var second = date.getSeconds();
    return year + '-' + month + '-' + day + '-' + hour + '-' + minute + '-' + second + '.jpg';
}

var imgsrc = [];
var imgalt = [];

function capture() {
    var video = document.getElementById("VID");
    var canvas = document.createElement("canvas");
    canvas.width = video.clientWidth;
    canvas.height = video.clientHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    var capture = document.getElementById("screenshot")
    capture.src = canvas.toDataURL('image/jpg');
    capture.style.width = "100%";
    var Time = moment();
    capture.alt = Time;
    imgsrc.push(capture.src)
    imgalt.push(capture.alt)

    canvas.toBlob(function (blob) {
        var formData = new FormData();
        formData.append('image', blob, Time);
        fetch('', {
            method: 'POST',
            body: formData
        })
            .then(response => {
                if (response.ok) {
                    console.log('图像上传成功');
                } else {
                    console.error('图像上传失败', response);
                }
            })
            .catch(error => {
                console.error('上传图像时发生错误', error);
            });
    }, 'image/jpg');
}

function delete_capture() {
    var capture = document.getElementById("screenshot");
    var name = capture.alt;
    const data = {
        delete: name
    }
    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => console.log(data))
        .catch(error => console.error('错误:', error));

    imgsrc.pop()
    imgalt.pop()
    capture.src = imgsrc[imgsrc.length - 1];
    capture.alt = imgalt[imgalt.length - 1];
}