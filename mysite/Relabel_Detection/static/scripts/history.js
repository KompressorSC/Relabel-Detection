function showTab(tabName) {
    // 隐藏所有选项卡内容
    let i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].classList.remove("active");
    }

    // 隐藏所有选项卡链接
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("active");
    }

    // 显示选中的选项卡内容和链接
    document.getElementById(tabName).classList.add("active");
}

function DELETE_HISTORY() {
    var deleteButtons = document.getElementsByClassName('delete-row');
    for (var i = 0; i < deleteButtons.length; i++) {
        deleteButtons[i].addEventListener('click', function (event) {
            // 阻止按钮的默认行为
            event.preventDefault();
            // 获取触发事件的按钮所在的行
            var row = event.target.parentNode.parentNode;
            // 得到要删除数据的id
            var spanElement = row.querySelector('td.hidden')
            var delete_id = spanElement.textContent || spanElement.innerText;
            // 得到要删除数据的模型名
            var history_type = row.parentNode.parentNode.parentNode.id;
            // 从表格中删除行
            row.parentNode.removeChild(row);
            // 发给后端
            var data = {
                type: history_type,
                id: delete_id
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
        });
    }
}
