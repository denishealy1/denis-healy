const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const statusEl = document.getElementById('status');
const restartBtn = document.getElementById('restart');

const gridSize = 20;
const tileCount = canvas.width / gridSize;

const directions = {
  ArrowUp: { x: 0, y: -1 },
  ArrowDown: { x: 0, y: 1 },
  ArrowLeft: { x: -1, y: 0 },
  ArrowRight: { x: 1, y: 0 },
  w: { x: 0, y: -1 },
  s: { x: 0, y: 1 },
  a: { x: -1, y: 0 },
  d: { x: 1, y: 0 }
};

let snake;
let food;
let direction;
let pendingDirection;
let score;
let gameOver;
let hasStarted;
let gameLoop;

function randomTile() {
  return {
    x: Math.floor(Math.random() * tileCount),
    y: Math.floor(Math.random() * tileCount)
  };
}

function spawnFood() {
  let nextFood = randomTile();
  while (snake.some((segment) => segment.x === nextFood.x && segment.y === nextFood.y)) {
    nextFood = randomTile();
  }
  food = nextFood;
}

function resetGame() {
  snake = [
    { x: 10, y: 10 },
    { x: 9, y: 10 },
    { x: 8, y: 10 }
  ];
  food = { x: 15, y: 10 };
  direction = { x: 1, y: 0 };
  pendingDirection = direction;
  score = 0;
  gameOver = false;
  hasStarted = false;
  scoreEl.textContent = '0';
  statusEl.textContent = 'Press any direction key to start.';
  draw();
}

function isOpposite(dirA, dirB) {
  return dirA.x + dirB.x === 0 && dirA.y + dirB.y === 0;
}

function update() {
  if (gameOver || !hasStarted) {
    draw();
    return;
  }

  direction = pendingDirection;

  const head = {
    x: snake[0].x + direction.x,
    y: snake[0].y + direction.y
  };

  const hitWall = head.x < 0 || head.y < 0 || head.x >= tileCount || head.y >= tileCount;
  const hitSelf = snake.some((segment) => segment.x === head.x && segment.y === head.y);

  if (hitWall || hitSelf) {
    gameOver = true;
    statusEl.textContent = 'Game over! Press Restart to play again.';
    draw();
    return;
  }

  snake.unshift(head);

  if (head.x === food.x && head.y === food.y) {
    score += 1;
    scoreEl.textContent = String(score);
    statusEl.textContent = 'Nice! Keep going.';
    spawnFood();
  } else {
    snake.pop();
  }

  draw();
}

function drawTile({ x, y }, color) {
  ctx.fillStyle = color;
  ctx.fillRect(x * gridSize, y * gridSize, gridSize - 1, gridSize - 1);
}

function draw() {
  ctx.fillStyle = '#0b1320';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  drawTile(food, '#ff8f8f');

  snake.forEach((segment, index) => {
    drawTile(segment, index === 0 ? '#9ef8b8' : '#53d48f');
  });
}

document.addEventListener('keydown', (event) => {
  const nextDir = directions[event.key];
  if (!nextDir || gameOver) {
    return;
  }

  if (!hasStarted) {
    hasStarted = true;
    statusEl.textContent = 'Game on!';
  }

  if (!isOpposite(nextDir, direction)) {
    pendingDirection = nextDir;
  }
});

restartBtn.addEventListener('click', () => {
  resetGame();
});

resetGame();
gameLoop = setInterval(update, 120);
