import streamlit as st
import chess
import chess.pgn
import chess.svg
import io
import html as html_lib

def run_pgn_viewer():
    st.header("PGN Viewer")

    #Session state
    if "move_index" not in st.session_state:
        st.session_state.move_index = 0
    if "last_pgn" not in st.session_state:
        st.session_state.last_pgn = ""
    if "flip" not in st.session_state:
        st.session_state.flip = False

    #input PGN
    pgn_text = st.text_area("Paste your PGN here:", height=180)
    if st.button("Load PGN"):
        st.session_state.move_index = 0
        st.session_state.last_pgn = pgn_text

    board = chess.Board()
    moves = []
    move_san_list = []

    if st.session_state.last_pgn.strip():
        try:
            pgn_io = io.StringIO(st.session_state.last_pgn)
            game = chess.pgn.read_game(pgn_io)

            if game is None:
                st.error("Invalid PGN — showing starting position.")
            else:
                moves = list(game.mainline_moves())
                temp_board = game.board()
                move_san_list = []
                for m in moves:
                    move_san_list.append(temp_board.san(m))
                    temp_board.push(m)

                #Clamp move_index
                st.session_state.move_index = max(0, min(st.session_state.move_index, len(moves)))

                #Navigation
                c_prev, c_next, c_restart = st.columns([1, 1, 1])
                with c_prev:
                    if st.button("Previous"):
                        if st.session_state.move_index > 0:
                            st.session_state.move_index -= 1
                with c_next:
                    if st.button("Next"):
                        if st.session_state.move_index < len(moves):
                            st.session_state.move_index += 1
                with c_restart:
                    if st.button("Restart"):
                        st.session_state.move_index = 0

                # Rebuild board
                board = game.board()
                for i in range(st.session_state.move_index):
                    board.push(moves[i])

                # Move counter
                full_move = (st.session_state.move_index + 1) // 2
                if st.session_state.move_index == 0:
                    st.markdown("**Starting position**")
                else:
                    turn = "White" if st.session_state.move_index % 2 == 1 else "Black"
                    st.markdown(f"**Move {full_move} — {turn} played**")

        except Exception as e:
            st.error(f"❌ Parsing error: {e}")

    #Render board
    svg_board = chess.svg.board(board=board, size=500, flipped=st.session_state.flip)
    st.components.v1.html(svg_board, height=520)

    #Flip board
    if st.button("🔄 Flip Board"):
        st.session_state.flip = not st.session_state.flip

    #Show PGN moves with highlight
    if move_san_list:
        highlight_idx = st.session_state.move_index - 1
        pieces = []
        for idx, mv in enumerate(move_san_list):
            safe_move = html_lib.escape(mv)
            if idx == highlight_idx:
                pieces.append(f"<mark>{safe_move}</mark>")
            else:
                pieces.append(safe_move)

        html_parts = []
        for i in range(0, len(pieces), 2):
            move_number = i // 2 + 1
            if i + 1 < len(pieces):
                html_parts.append(f"{move_number}. {pieces[i]} {pieces[i+1]}")
            else:
                html_parts.append(f"{move_number}. {pieces[i]}")

        html_content = "  &nbsp;&nbsp; ".join(html_parts)
        final_html = f"""
        <div style="font-family: monospace; font-size: 16px; line-height: 1.6; white-space: pre-wrap;">
            {html_content}
        </div>
        """

        st.markdown("---")
        st.markdown("### PGN Moves")
        st.markdown(final_html, unsafe_allow_html=True)
