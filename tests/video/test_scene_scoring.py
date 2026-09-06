"""Pruebas de la calificación de escenas sobre clips generados en el momento.

En simple: comprueban que una toma bien expuesta puntúa más que una oscura, que
una cámara quieta puntúa más estable que una que se mueve, que puntuar una escena
larga no cuesta más que una corta —porque no se recorre el clip— y que una escena
ilegible se aparta sin tumbar el resto.
"""

import subprocess
from pathlib import Path

import pytest

from media_optimizer.core import CorruptMediaError, Scene, SceneScore
from media_optimizer.ingest import filesystem
from media_optimizer.photo import ExposureThresholds
from media_optimizer.video import MUESTRAS_POR_ESCENA, is_available, score_scene, score_scenes
from media_optimizer.video.scene_scoring import _momentos

_SIN_BINARIO = not is_available()

_CRITERIOS = ExposureThresholds(
    brightness_target=128.0,
    crushed_shadows_weight=0.5,
    blown_highlights_weight=0.5,
    publishable_min_score=0.7,
    support_min_score=0.4,
)


def _clip(destino: Path, fuente: str, segundos: int = 4) -> None:
    """Genera un clip sintético a partir de una fuente de la herramienta de video."""
    binario = filesystem.find_executable("ffmpeg")
    assert binario is not None
    filesystem.make_directory(destino.parent)
    subprocess.run(  # noqa: S603 - ruta absoluta, lista de argumentos, sin shell
        [
            binario,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"{fuente}:s=320x240:d={segundos}:r=15",
            "-pix_fmt",
            "yuv420p",
            filesystem.system_path(destino),
        ],
        capture_output=True,
        check=True,
        timeout=120,
    )


class TestMomentosDeMuestreo:
    """Se pueden comprobar sin abrir ningún video."""

    def test_las_posiciones_caen_dentro_de_la_escena(self) -> None:
        escena = Scene(index=0, start_seconds=2.0, end_seconds=8.0)
        for momento in _momentos(escena, 5):
            assert escena.start_seconds < momento < escena.end_seconds

    def test_son_siempre_las_mismas_para_la_misma_escena(self) -> None:
        escena = Scene(index=0, start_seconds=0.0, end_seconds=10.0)
        assert _momentos(escena, 5) == _momentos(escena, 5)

    def test_estan_repartidas_y_en_orden(self) -> None:
        momentos = _momentos(Scene(index=0, start_seconds=0.0, end_seconds=6.0), 5)
        assert len(momentos) == 5
        assert list(momentos) == sorted(momentos)

    def test_una_sola_muestra_cae_en_el_centro(self) -> None:
        (momento,) = _momentos(Scene(index=0, start_seconds=0.0, end_seconds=4.0), 1)
        assert momento == pytest.approx(2.0)

    def test_pedir_cero_muestras_igual_mira_un_cuadro(self) -> None:
        assert len(_momentos(Scene(index=0, start_seconds=0.0, end_seconds=4.0), 0)) == 1


@pytest.mark.skipif(_SIN_BINARIO, reason="el binario de video no está instalado")
class TestCalificacionSobreClipsReales:
    def test_una_escena_bien_expuesta_puntua_mas_que_una_oscura(self, tmp_path: Path) -> None:
        clara, oscura = tmp_path / "clara.mp4", tmp_path / "oscura.mp4"
        _clip(clara, "color=c=gray")
        _clip(oscura, "color=c=black")
        escena = Scene(index=0, start_seconds=0.5, end_seconds=3.5)

        buena = score_scene(clara, escena, _CRITERIOS)
        mala = score_scene(oscura, escena, _CRITERIOS)

        assert buena.exposure > mala.exposure

    def test_una_camara_quieta_puntua_mas_estable_que_una_que_cambia(self, tmp_path: Path) -> None:
        quieto, movido = tmp_path / "quieto.mp4", tmp_path / "movido.mp4"
        _clip(quieto, "color=c=gray")
        _clip(movido, "testsrc2=alpha=0")
        escena = Scene(index=0, start_seconds=0.5, end_seconds=3.5)

        assert (
            score_scene(quieto, escena, _CRITERIOS).stability
            > score_scene(movido, escena, _CRITERIOS).stability
        )

    def test_no_se_leen_mas_cuadros_que_las_muestras_pedidas(self, tmp_path: Path) -> None:
        """El charter prohíbe cargar el clip entero; se salta a las posiciones."""
        largo = tmp_path / "largo.mp4"
        _clip(largo, "color=c=gray", segundos=20)
        escena = Scene(index=0, start_seconds=0.5, end_seconds=19.5)

        assert score_scene(largo, escena, _CRITERIOS).sampled_frames <= MUESTRAS_POR_ESCENA

    def test_es_determinista(self, tmp_path: Path) -> None:
        clip = tmp_path / "determinista.mp4"
        _clip(clip, "color=c=gray")
        escena = Scene(index=0, start_seconds=0.5, end_seconds=3.5)

        assert score_scene(clip, escena, _CRITERIOS) == score_scene(clip, escena, _CRITERIOS)

    def test_una_escena_muy_corta_se_puntua_igual(self, tmp_path: Path) -> None:
        clip = tmp_path / "corta.mp4"
        _clip(clip, "color=c=gray")
        escena = Scene(index=0, start_seconds=1.0, end_seconds=1.2)

        assert score_scene(clip, escena, _CRITERIOS).sampled_frames >= 1

    def test_califica_todas_las_escenas_en_orden(self, tmp_path: Path) -> None:
        clip = tmp_path / "varias.mp4"
        _clip(clip, "color=c=gray", segundos=6)
        escenas = (
            Scene(index=0, start_seconds=0.5, end_seconds=2.0),
            Scene(index=1, start_seconds=2.0, end_seconds=5.5),
        )

        notas = score_scenes(clip, escenas, _CRITERIOS)

        assert [n.scene_index for n in notas] == [0, 1]

    def test_un_clip_ilegible_aparta_esa_escena(self, tmp_path: Path) -> None:
        roto = tmp_path / "roto.mp4"
        filesystem.write_bytes(roto, b"esto no es un video")

        with pytest.raises(CorruptMediaError):
            score_scene(roto, Scene(index=0, start_seconds=0.0, end_seconds=1.0), _CRITERIOS)

    def test_un_clip_inexistente_aparta_esa_escena(self, tmp_path: Path) -> None:
        with pytest.raises(CorruptMediaError):
            score_scene(
                tmp_path / "no_existe.mp4",
                Scene(index=0, start_seconds=0.0, end_seconds=1.0),
                _CRITERIOS,
            )

    def test_funciona_con_una_ruta_larga(self, tmp_path: Path) -> None:
        clip = tmp_path.joinpath(*(("z" * 40,) * 8)) / "largo.mp4"
        _clip(clip, "color=c=gray")
        assert len(str(clip)) > 260

        assert score_scene(clip, Scene(index=0, start_seconds=0.5, end_seconds=3.5), _CRITERIOS)


class TestContratoDeLaNota:
    def test_la_nota_general_promedia_los_componentes_medidos(self) -> None:
        nota = SceneScore(scene_index=0, exposure=0.8, stability=0.6, sampled_frames=5)
        assert nota.overall == pytest.approx(0.7)

    def test_anadir_un_componente_no_cambiaria_el_contrato(self) -> None:
        """La nitidez entrará como un componente más cuando su ADR cierre."""
        nota = SceneScore(scene_index=0, exposure=1.0, stability=1.0, sampled_frames=3)
        assert len(nota.components) == 2
        assert nota.overall == pytest.approx(sum(nota.components) / len(nota.components))


@pytest.mark.skipif(_SIN_BINARIO, reason="el binario de video no está instalado")
class TestEstabilidad:
    def test_con_una_sola_muestra_sigue_midiendo_el_movimiento(self, tmp_path: Path) -> None:
        """Basta un momento: se compara ese cuadro con el que le sigue."""
        clip = tmp_path / "una_muestra.mp4"
        _clip(clip, "testsrc2=alpha=0")

        nota = score_scene(
            clip, Scene(index=0, start_seconds=0.5, end_seconds=3.5), _CRITERIOS, samples=1
        )

        assert nota.sampled_frames == 1
        assert nota.stability < 1.0

    def test_se_mide_entre_cuadros_contiguos_no_entre_muestras(self, tmp_path: Path) -> None:
        """Sobre material real, comparar muestras separadas daba cero a casi todo.

        Dos muestras a un segundo de distancia difieren mucho aunque la cámara
        estuviera quieta, así que la métrica no distinguía nada. Con cuadros
        contiguos, subir el número de muestras no puede desplomar la estabilidad.
        """
        clip = tmp_path / "contiguos.mp4"
        _clip(clip, "color=c=gray", segundos=8)
        escena = Scene(index=0, start_seconds=0.5, end_seconds=7.5)

        pocas = score_scene(clip, escena, _CRITERIOS, samples=2)
        muchas = score_scene(clip, escena, _CRITERIOS, samples=8)

        assert pocas.stability == muchas.stability == 1.0


@pytest.mark.skipif(_SIN_BINARIO, reason="el binario de video no está instalado")
class TestDegradacionParcial:
    """Una escena mal delimitada se puntúa con lo que haya, sin apartarse."""

    def test_una_escena_que_sobresale_del_clip_usa_los_cuadros_que_existen(
        self, tmp_path: Path
    ) -> None:
        clip = tmp_path / "corto.mp4"
        _clip(clip, "color=c=gray", segundos=3)

        nota = score_scene(clip, Scene(index=0, start_seconds=0.5, end_seconds=6.0), _CRITERIOS)

        assert 1 <= nota.sampled_frames < MUESTRAS_POR_ESCENA
        assert 0.0 <= nota.stability <= 1.0
