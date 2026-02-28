/**
 * 3 en Raya - DoTerra Edition
 * by Susanna Valla (Ecuador)
 */

'use strict';

// ===== Constants =====
const PLAYERS = {
  X: { id: 'x', name: 'Lavanda', icon: 'Good%20Lavanda.jpg', color: 'good' },
  O: { id: 'o', name: 'Píldorín', icon: 'Bad%20Pill.jpg', color: 'bad' }
};

const WIN_COMBINATIONS = [
  [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
  [0, 3, 6], [1, 4, 7], [2, 5, 8], // Columns
  [0, 4, 8], [2, 4, 6]             // Diagonals
];

// ===== Game State =====
const state = {
  board: Array(9).fill(null),
  currentPlayer: PLAYERS.X,
  gameOver: false,
  scores: { x: 0, o: 0, draws: 0 },
  winningCombo: null
};

// ===== DOM Elements =====
const elements = {
  cells: document.querySelectorAll('.cell'),
  playerCards: {
    x: document.getElementById('player-x'),
    o: document.getElementById('player-o')
  },
  turnImg: document.getElementById('turn-img'),
  turnName: document.getElementById('turn-name'),
  scores: {
    x: document.getElementById('score-x'),
    o: document.getElementById('score-o'),
    draws: document.getElementById('score-draws')
  },
  resetBtn: document.getElementById('reset-btn'),
  modal: document.getElementById('modal'),
  modalImg: document.getElementById('modal-img'),
  modalTitle: document.getElementById('modal-title'),
  modalMessage: document.getElementById('modal-message'),
  modalBtn: document.getElementById('modal-btn')
};

// ===== Initialization =====
function init() {
  resetGame();
  attachEventListeners();
  updateUI();
}

function resetGame() {
  state.board.fill(null);
  state.currentPlayer = PLAYERS.X;
  state.gameOver = false;
  state.winningCombo = null;
  
  elements.cells.forEach(cell => {
    cell.innerHTML = '';
    cell.className = 'cell';
    cell.disabled = false;
    cell.dataset.player = '';
  });
  
  hideModal();
}

function attachEventListeners() {
  elements.cells.forEach((cell, index) => {
    cell.addEventListener('click', () => handleCellClick(index));
  });
  
  elements.resetBtn.addEventListener('click', resetGame);
  elements.modalBtn.addEventListener('click', resetGame);
  
  // Close modal on backdrop click
  document.querySelector('.modal-backdrop')?.addEventListener('click', hideModal);
  
  // Keyboard support for modal
  document.addEventListener('keydown', handleKeyDown);
}

// ===== Game Logic =====
function handleCellClick(index) {
  if (state.gameOver || state.board[index]) return;
  
  // Place piece
  state.board[index] = state.currentPlayer.id;
  renderCell(index);
  
  // Check for win
  const winCombo = checkWin(state.currentPlayer.id);
  if (winCombo) {
    handleWin(winCombo);
    return;
  }
  
  // Check for draw
  if (checkDraw()) {
    handleDraw();
    return;
  }
  
  // Switch player
  switchPlayer();
}

function renderCell(index) {
  const cell = elements.cells[index];
  const player = state.currentPlayer;
  
  const img = document.createElement('img');
  img.src = player.icon;
  img.alt = player.name;
  img.loading = 'lazy';
  
  cell.appendChild(img);
  cell.classList.add('taken');
  cell.dataset.player = player.id;
  cell.disabled = true;
}

function checkWin(playerId) {
  return WIN_COMBINATIONS.find(combo => 
    combo.every(index => state.board[index] === playerId)
  ) || null;
}

function checkDraw() {
  return state.board.every(cell => cell !== null);
}

function handleWin(winCombo) {
  state.gameOver = true;
  state.winningCombo = winCombo;
  state.scores[state.currentPlayer.id]++;
  
  // Highlight winning cells
  winCombo.forEach(index => {
    elements.cells[index].classList.add('win');
  });
  
  updateScoreboard();
  
  // Show modal after animation
  setTimeout(() => {
    showWinModal();
  }, 600);
}

function handleDraw() {
  state.gameOver = true;
  state.scores.draws++;
  updateScoreboard();
  
  setTimeout(() => {
    showDrawModal();
  }, 300);
}

function switchPlayer() {
  state.currentPlayer = state.currentPlayer === PLAYERS.X ? PLAYERS.O : PLAYERS.X;
  updateUI();
}

// ===== UI Updates =====
function updateUI() {
  updateActivePlayer();
  updateTurnIndicator();
}

function updateActivePlayer() {
  elements.playerCards.x.classList.toggle('active', state.currentPlayer === PLAYERS.X);
  elements.playerCards.o.classList.toggle('active', state.currentPlayer === PLAYERS.O);
}

function updateTurnIndicator() {
  elements.turnImg.src = state.currentPlayer.icon;
  elements.turnImg.alt = state.currentPlayer.name;
  elements.turnName.textContent = state.currentPlayer.name;
  elements.turnName.style.color = `var(--color-${state.currentPlayer.color})`;
}

function updateScoreboard() {
  elements.scores.x.textContent = state.scores.x;
  elements.scores.o.textContent = state.scores.o;
  elements.scores.draws.textContent = state.scores.draws;
}

// ===== Modal Functions =====
function showWinModal() {
  const winner = state.currentPlayer;
  
  elements.modalImg.src = winner.icon;
  elements.modalImg.alt = winner.name;
  elements.modalTitle.textContent = `¡${winner.name} gana!`;
  elements.modalMessage.innerHTML = winner === PLAYERS.X 
    ? '¡El bien prevalece!' 
    : '¡El mal triunfa esta vez!';
  
  showModal();
}

function showDrawModal() {
  elements.modalImg.style.display = 'none';
  elements.modalTitle.textContent = '¡Empate!';
  elements.modalMessage.textContent = '¡La batalla continúa!';
  
  showModal();
}

function showModal() {
  elements.modal.hidden = false;
  elements.modalBtn.focus();
  document.body.style.overflow = 'hidden';
}

function hideModal() {
  elements.modal.hidden = true;
  elements.modalImg.style.display = 'block';
  document.body.style.overflow = '';
}

// ===== Keyboard Support =====
function handleKeyDown(e) {
  if (e.key === 'Escape' && !elements.modal.hidden) {
    hideModal();
  }
  
  if (e.key === 'Enter' && !elements.modal.hidden) {
    resetGame();
  }
}

// ===== Start Game =====
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
