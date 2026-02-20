// Utility to convert mathematical notation to HTML with superscripts/subscripts
export const formatMathNotation = (text) => {
  if (!text) return '';
  
  let formatted = text;
  
  // Convert powers: x^2 or x^{2} → x<sup>2</sup>
  formatted = formatted.replace(/(\w)\^{?(\w+)}?/g, '$1<sup>$2</sup>');
  
  // Convert subscripts: H_2 or H_{2} → H<sub>2</sub>
  formatted = formatted.replace(/(\w)_{?(\w+)}?/g, '$1<sub>$2</sub>');
  
  return formatted;
};

// React component to render math notation
export const MathText = ({ children }) => {
  const formatted = formatMathNotation(children);
  return <span dangerouslySetInnerHTML={{ __html: formatted }} />;
};
