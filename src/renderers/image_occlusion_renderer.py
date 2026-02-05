"""Renderer for image occlusion cards."""

import re
import json
from typing import Dict, List
from ..models import Note, NoteModel
from .base import BaseNoteRenderer


class ImageOcclusionRenderer(BaseNoteRenderer):
    """Renderer for image occlusion cards with interactive masking."""

    def can_render(self, note_model: NoteModel) -> bool:
        """Check if this is an image occlusion note model."""
        return "image" in note_model.name.lower() and "occlusion" in note_model.name.lower()

    def render_card(
        self,
        note: Note,
        note_model: NoteModel,
        template_idx: int = 0
    ) -> Dict[str, str]:
        """
        Render an image occlusion card.

        Args:
            note: Note to render
            note_model: Note model with templates
            template_idx: Template index (usually 0)

        Returns:
            Dictionary with "front", "back", and "css" keys
        """
        if template_idx >= len(note_model.tmpls):
            template_idx = 0

        template = note_model.tmpls[template_idx]

        # Build field map
        fields = self._build_field_map(note, note_model)

        # Extract shape data from Occlusion field
        occlusion_field = fields.get("Occlusion", "")
        shapes = self._parse_occlusion_shapes(occlusion_field)

        # Render templates
        front_html = self.template_engine.render(
            template.qfmt,
            fields,
            note.tags,
            is_answer=False
        )

        back_html = self.template_engine.render(
            template.afmt,
            fields,
            note.tags,
            is_answer=True,
            front_side_html=front_html
        )

        # Inject our custom image occlusion script
        front_html = self._inject_io_script(front_html, shapes, show_answer=False)
        back_html = self._inject_io_script(back_html, shapes, show_answer=True)

        return {
            "front": front_html,
            "back": back_html,
            "css": note_model.css
        }

    def _parse_occlusion_shapes(self, occlusion_field: str) -> List[Dict]:
        """
        Parse image-occlusion coordinate syntax.

        Parses patterns like:
        {{c1::image-occlusion:rect:left=.592:top=.4403:width=.0786:height=.0963:oi=1}}

        Args:
            occlusion_field: Field content with occlusion data

        Returns:
            List of shape dictionaries
        """
        pattern = r'\{\{c(\d+)::image-occlusion:(\w+):(.*?)\}\}'
        shapes = []

        for match in re.finditer(pattern, occlusion_field):
            cloze_num = int(match.group(1))
            shape_type = match.group(2)
            params_str = match.group(3)

            # Parse parameters
            params = {}
            for param in params_str.split(':'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value

            shapes.append({
                "cloze": cloze_num,
                "type": shape_type,
                "params": params
            })

        return shapes

    def _inject_io_script(self, html: str, shapes: List[Dict], show_answer: bool) -> str:
        """
        Inject image occlusion JavaScript into HTML.

        Args:
            html: Template HTML
            shapes: List of shape definitions
            show_answer: True if showing answer (revealed)

        Returns:
            HTML with JavaScript injected
        """
        # Generate the script
        io_script = self._generate_io_script(shapes, show_answer)

        # Replace anki.imageOcclusion.setup() if present
        if "anki.imageOcclusion.setup()" in html:
            html = html.replace("anki.imageOcclusion.setup()", io_script)
        # Otherwise, inject before closing script tag if present
        elif "</script>" in html:
            html = html.replace("</script>", f"{io_script}\n</script>", 1)
        # Otherwise, add script tag at end
        else:
            html += f"\n<script>\n{io_script}\n</script>"

        return html

    def _generate_io_script(self, shapes: List[Dict], show_answer: bool) -> str:
        """
        Generate JavaScript to render shapes on canvas.

        Args:
            shapes: List of shape definitions
            show_answer: True if showing answer

        Returns:
            JavaScript code as string
        """
        shapes_json = json.dumps(shapes)
        show_answer_json = json.dumps(show_answer)

        return f"""
(function() {{
    const canvas = document.getElementById('image-occlusion-canvas');
    const container = document.getElementById('image-occlusion-container');

    if (!canvas || !container) {{
        console.warn('Image occlusion elements not found');
        return;
    }}

    const img = container.querySelector('img');

    if (!img) {{
        console.warn('Image not found in container');
        return;
    }}

    function drawShapes() {{
        canvas.width = img.width || img.naturalWidth;
        canvas.height = img.height || img.naturalHeight;

        // Position canvas over image
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.pointerEvents = 'none';

        const ctx = canvas.getContext('2d');

        const shapes = {shapes_json};
        const showAnswer = {show_answer_json};

        shapes.forEach(shape => {{
            const params = shape.params;
            const x = parseFloat(params.left || 0) * canvas.width;
            const y = parseFloat(params.top || 0) * canvas.height;
            const w = parseFloat(params.width || 0) * canvas.width;
            const h = parseFloat(params.height || 0) * canvas.height;

            // Different colors for question vs answer
            if (showAnswer) {{
                // Answer: semi-transparent red highlight
                ctx.fillStyle = 'rgba(255, 142, 142, 0.5)';
            }} else {{
                // Question: solid occlusion (yellow/beige)
                ctx.fillStyle = '#ffeba2';
            }}

            ctx.strokeStyle = '#212121';
            ctx.lineWidth = 2;

            if (shape.type === 'rect') {{
                ctx.fillRect(x, y, w, h);
                ctx.strokeRect(x, y, w, h);
            }} else if (shape.type === 'ellipse') {{
                ctx.beginPath();
                ctx.ellipse(x + w/2, y + h/2, w/2, h/2, 0, 0, 2 * Math.PI);
                ctx.fill();
                ctx.stroke();
            }}
        }});
    }}

    // Make container relative for absolute positioning of canvas
    container.style.position = 'relative';
    container.style.display = 'inline-block';

    // Draw when image loads
    if (img.complete) {{
        drawShapes();
    }} else {{
        img.onload = drawShapes;
    }}
}})();
"""
