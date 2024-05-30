function ShowConfirmWindow() {
    document.getElementById('confirm-window').style.display = 'block';
}

// 隐藏确认弹窗
function HideConfirmWindow() {
    document.getElementById('confirm-window').style.display = 'none';
}

function SendOperation(id) {
    const data = {
        operation: id
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
}