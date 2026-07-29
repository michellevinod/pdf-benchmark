from pydantic import ValidationError as PydanticValidationError

from validation.exceptions import ValidationError
from validation.schemas import NormalizedDocument


class SchemaValidator:

    @staticmethod
    def validate(
        document: dict,
    ) -> NormalizedDocument:
        """
        Validates a normalized document against
        the benchmark schema.
        """

        try:
            return NormalizedDocument.model_validate(
                document,
            )

        except PydanticValidationError as error:
            raise ValidationError(
                str(error)
            ) from error