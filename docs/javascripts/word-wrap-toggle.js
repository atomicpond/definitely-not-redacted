// Word wrap toggle for document text blocks
document.addEventListener('DOMContentLoaded', function() {
  // Find all code blocks in document pages
  const codeBlocks = document.querySelectorAll('pre code');

  if (codeBlocks.length === 0) return;

  // Add toggle button to each code block
  codeBlocks.forEach(function(codeBlock) {
    const pre = codeBlock.parentElement;

    // Create toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'word-wrap-toggle';
    toggleBtn.innerHTML = '📄 Toggle Word Wrap';
    toggleBtn.title = 'Toggle word wrapping for this text';

    // Insert button before the pre element
    pre.parentNode.insertBefore(toggleBtn, pre);

    // Toggle word wrap on click
    toggleBtn.addEventListener('click', function() {
      if (pre.style.whiteSpace === 'pre-wrap') {
        pre.style.whiteSpace = 'pre';
        pre.style.wordWrap = 'normal';
        pre.style.overflowX = 'auto';
      } else {
        pre.style.whiteSpace = 'pre-wrap';
        pre.style.wordWrap = 'break-word';
        pre.style.overflowX = 'hidden';
      }
    });
  });
});
