document.addEventListener('DOMContentLoaded', function() {
    const gameButton = document.getElementById('gameButton');
    const scoreDisplay = document.getElementById('score');
    let score = 0;

    gameButton.addEventListener('click', function() {
        const maxX = document.getElementById('gameArea').clientWidth - gameButton.clientWidth;
        const maxY = document.getElementById('gameArea').clientHeight - gameButton.clientHeight;

        const randomX = Math.random() * maxX;
        const randomY = Math.random() * maxY;

        gameButton.style.left = randomX + 'px';
        gameButton.style.top = randomY + 'px';

        score++;
        scoreDisplay.textContent = score;
    });
});