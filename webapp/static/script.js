document.addEventListener("DOMContentLoaded", () => {
  const btnStart = document.getElementById("startBtn");
  const btnReset = document.getElementById("resetBtn");
  const countdownEl = document.getElementById("countdown");
  const visual1 = document.getElementById("visual1");
  const visual2 = document.getElementById("visual2");
  const visual3 = document.getElementById("visual3");

  if (!window.dynamic || !dynamic.active) {
    if (countdownEl) countdownEl.textContent = "-";
    return;
  }
  const initial = dynamic.steps[0].visual;
  visual1.textContent = initial.row1.join('   ');
  visual2.textContent = initial.row2.join('   ');
  visual3.textContent = initial.row3.join('   ');
  countdownEl.textContent = dynamic.duration;

  let timer = null;
  function startSequence() {
    let remaining = dynamic.duration;
    btnStart.disabled = true;
    btnReset.disabled = false;
    countdownEl.textContent = remaining;
    timer = setInterval(() => {
      remaining -= 1;
      if (remaining < 0) {
        clearInterval(timer);
        const closing = dynamic.steps[2].visual;
        visual1.textContent = closing.row1.join('   ');
        visual2.textContent = closing.row2.join('   ');
        visual3.textContent = closing.row3.join('   ');
        countdownEl.textContent = 0;
        btnStart.disabled = false;
        return;
      }
      countdownEl.textContent = remaining;
      const openIdx = dynamic.open_lane - 1;
    }, 1000);
  }

  function resetSequence(){
    if (timer) clearInterval(timer);
    btnStart.disabled = false;
    btnReset.disabled = true;
    countdownEl.textContent = dynamic.duration;
    const initial = dynamic.steps[0].visual;
    visual1.textContent = initial.row1.join('   ');
    visual2.textContent = initial.row2.join('   ');
    visual3.textContent = initial.row3.join('   ');
  }

  btnStart.addEventListener('click', startSequence);
  btnReset.addEventListener('click', resetSequence);

  // disable reset initially
  btnReset.disabled = true;
});
