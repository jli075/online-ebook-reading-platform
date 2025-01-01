function likeUnlike(event, element) {
    // Prevent the default link behavior
    event.preventDefault();

    var book_url = element.getAttribute('data-like-url');
    var path_arr = book_url.split("/");
    var action = path_arr.pop();
    var bookId = path_arr.pop();

    fetch(book_url, {
        method: 'POST',  // Use POST to match Flask route
        headers: {
            'Content-Type': 'application/json',  // Ensure correct content type for JSON
        },
        body: JSON.stringify({
            book_id: bookId,
            action: action
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Optionally update the UI (e.g., change button state or icon)
                like_element = document.getElementById(`like-count-${bookId}`);
                like_count = parseInt(like_element.getAttribute('like-count'));

                if (action === 'like') {
                    element.setAttribute('data-action', 'unlike');
                    element.setAttribute('data-like-url', `/like/${bookId}/unlike`);
                    element.setAttribute('class', 'unlike-button');
                    element.innerHTML = `<svg class="bi" style="color: red" width="1em" height="1em" fill="currentColor"><use xlink:href="/bootstrap/static/icons/bootstrap-icons.svg#heart-fill"></use></svg>`;
                    like_count += 1;

                } else {
                    element.setAttribute('data-action', 'like');
                    element.setAttribute('data-like-url', `/like/${bookId}/like`);
                    element.setAttribute('class', 'like-button');
                    element.innerHTML = `<svg class="bi" style="color: gray" width="1em" height="1em" fill="currentColor"><use xlink:href="/bootstrap/static/icons/bootstrap-icons.svg#heart"></use></svg>`;
                    like_count -= 1;
                }
                if (like_count == 1) {
                    like_element.innerText = `${like_count} like`;
                }
                else {
                    like_element.innerText = `${like_count} likes`;
                }
                like_element.setAttribute("like-count", `${like_count}`);
            }
            else {
                console.error('Action failed:', data);
            }
        })
        .catch(error => {
            console.error('Error during fetch:', error);
        });
}