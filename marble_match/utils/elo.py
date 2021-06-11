import logging

logger = logging.getLogger(f'marble_match.{__name__}')

k_factor = 32


def get_expected_scores(player1_rank: float, player2_rank: float) -> list:
    logger.debug(f'get_expected_scores: {player1_rank}, {player2_rank}')

    # Transformed rating
    player1_transformed = 10**(player1_rank/400)
    player2_transformed = 10**(player2_rank / 400)

    # Expected score
    player1_expected = player1_transformed / (player1_transformed + player2_transformed)
    player2_expected = player2_transformed / (player1_transformed + player2_transformed)

    logger.debug(f'player1_expected: {player1_expected}, player2_expected: {player2_expected}')

    return [player1_expected, player2_expected]


# score: 1 wins, 0.5 draw, 0 lose
def get_updated_scores(player1_rank: float, player2_rank: float, player1_score: float, player2_score: float,
                       _k_factor: int = k_factor) -> list:
    logger.debug(f'get_updated_scores: {player1_rank}, {player2_rank}, {player1_score}, {player2_score}')

    expected_scores = get_expected_scores(player1_rank, player2_rank)

    player1_updated = player1_rank + _k_factor * (player1_score - expected_scores[0])
    player2_updated = player2_rank + _k_factor * (player2_score - expected_scores[1])

    logger.debug(f'player1_updated: {player1_updated}, player2_updated: {player2_updated}')

    return [player1_updated, player2_updated]
