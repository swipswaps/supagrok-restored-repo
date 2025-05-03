document.querySelector('button').onclick = () => {
  fetch('/launchers/launch_nobara.sh')
    .then(res => console.log("Launcher triggered"))
    .catch(err => console.error("Launcher failed", err));
};
