import io
import pdfplumber
import fitz  # PyMuPDF

class WhiteTextDetector:
    """
    Detects invisible/white text by comparing rendering layers
    """
    
    def detect_white_text(self, pdf_bytes: bytes) -> dict:
        """
        Compare visible text (rendering) vs all text (extraction)
        Difference = hidden text
        """
        
        # Layer 1: Visible text (what humans see)
        visible_text = self._extract_visible_text(pdf_bytes)
        
        # Layer 2: All text (including invisible)
        all_text = self._extract_all_text(pdf_bytes)
        
        # Find hidden content
        visible_words = set(visible_text.lower().split())
        all_words = set(all_text.lower().split())
        hidden_words = all_words - visible_words
        
        # Analyze suspiciousness
        return self._analyze_hidden_content(hidden_words, all_text)
    
    def _extract_visible_text(self, pdf_bytes: bytes) -> str:
        """
        Extract only visually rendered text
        Uses pdfplumber which respects text rendering
        """
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                visible_text = ""
                for page in pdf.pages:
                    # Extract text with layout awareness
                    text = page.extract_text(
                        layout=True,
                        x_tolerance=3,
                        y_tolerance=3
                    )
                    if text:
                        visible_text += text + "\n"
                
                return visible_text
        except Exception as e:
            # Fallback to all text if rendering fails
            return self._extract_all_text(pdf_bytes)
    
    def _extract_all_text(self, pdf_bytes: bytes) -> str:
        """
        Extract ALL text including invisible layers
        Uses PyMuPDF which gets everything
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            all_text = ""
            for page in doc:
                # Get all text regardless of visibility
                text = page.get_text("text")
                all_text += text + "\n"
            
            doc.close()
            return all_text
        except Exception as e:
            return ""
    
    def _analyze_hidden_content(self, hidden_words: set, full_text: str) -> dict:
        """
        Determine if hidden text is malicious
        """
        
        # Suspicious keywords that shouldn't be hidden
        suspicious_keywords = [
            "hire", "perfect", "candidate", "qualified", "expert",
            "ignore", "instructions", "approve", "score", "100",
            "python", "java", "javascript", "react", "node", "pytorch", "tensorflow", # Tech keywords
            "engineer", "developer", "manager", "lead", "senior",
            "faang", "google", "meta", "amazon", "apple", "netflix", # Prestige stuffing
            "chatgpt", "openai", "generated", "ai", "llm" # Bot signatures
        ]
        
        # Find suspicious hidden words (using substring match to catch joined words)
        suspicious_matches = []
        for word in hidden_words:
            word_lower = word.lower()
            if any(keyword in word_lower for keyword in suspicious_keywords):
                suspicious_matches.append(word)
        
        # Thresholds
        hidden_count = len(hidden_words)
        suspicious_count = len(suspicious_matches)
        
        # Calculate hidden ratio (hidden vs total)
        all_words_list = full_text.lower().split()
        total_word_count = len(all_words_list)
        hidden_ratio = hidden_count / total_word_count if total_word_count > 0 else 0
        
        # Determine severity
        # If NEARLY ALL text is "hidden" (e.g. > 90%), it's almost certainly an 
        # extraction tool failure (pdfplumber vs fitz) rather than malicious stuffing.
        if hidden_ratio > 0.90 and total_word_count > 50:
            severity = "low"
            action = "proceed"
            explanation = f"Detected extraction tool discrepancy ({hidden_count} words). Not malicious."
        elif suspicious_count > 3 or hidden_count > 80:
            severity = "critical"
            action = "immediate_blacklist"
            explanation = f"Found {hidden_count} hidden words, {suspicious_count} suspicious"
        elif suspicious_count > 1 or hidden_count > 40:
            severity = "high"
            action = "queue_for_review"
            explanation = f"Found {hidden_count} hidden words, {suspicious_count} suspicious"
        elif hidden_count > 15:
            severity = "medium"
            action = "flag_for_review"
            explanation = f"Found {hidden_count} hidden words"
        else:
            severity = "low"
            action = "proceed"
            explanation = f"Negligible hidden content ({hidden_count} words)"

        return {
            "white_text_detected": hidden_count > 20,
            "severity": severity,
            "hidden_word_count": hidden_count,
            "suspicious_matches": list(suspicious_matches)[:10],
            "action": action,
            "explanation": explanation
        }

