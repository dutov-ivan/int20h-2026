from enum import Enum, IntEnum
from pydantic import AfterValidator, BaseModel, Field, ConfigDict
from typing import Annotated, Literal
import phonenumbers


class StudyYear(IntEnum):
    YEAR_1 = 1
    YEAR_2 = 2
    YEAR_3 = 3
    YEAR_4 = 4
    YEAR_5 = 5
    YEAR_6 = 6

    def __str__(self):
        if self <= 4:
            return f"{self.value} курс"
        else:
            return f"{self.value} курс магістр"


class ParticipantStudyInfo(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    alma_mater: Annotated[
        str, Field(description="The educational institution the user graduated from")
    ]
    study_year: Annotated[
        StudyYear, Field(description="The current year of study of the user")
    ]


class ParticipantTeamInfo(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    is_team_lead: Annotated[
        bool, Field(description="Whether the user is the team lead or not")
    ]
    team_name: Annotated[str, Field(description="The name of the user's team")]


class Category(str, Enum):
    WEB = "Web"
    DATA_SCIENCE = "Data Science"
    UI_UX = "UI/UX"
    AI_ML = "AI/ML"


def normalize_phone_number(number: str) -> str:
    try:
        parsed_number = phonenumbers.parse(number, None)
    except phonenumbers.NumberParseException as e:
        raise ValueError(f"Invalid phone number: {e}")

    if not phonenumbers.is_possible_number(parsed_number):
        raise ValueError("Invalid phone number")
    return phonenumbers.format_number(
        parsed_number, phonenumbers.PhoneNumberFormat.E164
    )


NormalizedPhone = Annotated[str, AfterValidator(normalize_phone_number)]


class Form(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: Annotated[str, Field(description="The full name of the user")]

    age: Annotated[int, Field(description="The age of the user in years", ge=0, le=120)]

    phone_number: Annotated[
        NormalizedPhone, Field(description="The phone number of the user")
    ]

    email: Annotated[str, Field(description="The email address of the user")]

    study_info: Annotated[
        ParticipantStudyInfo | None,
        Field(description="Information about the user's university, if applicable"),
    ] = None

    study_year: Annotated[
        StudyYear, Field(description="The current year of study of the user")
    ]

    category: Annotated[
        Category, Field(description="The category of interest for the user")
    ]

    technologies: Annotated[
        str, Field(description="Technologies the user is proficient at")
    ]

    is_looking_for_job: Annotated[
        bool, Field(description="Whether the user is looking for a job or not")
    ]

    is_participating_offline: Annotated[
        bool,
        Field(
            description="Whether the user is participating in offline hackathon or not"
        ),
    ]

    has_team: Annotated[bool, Field(description="Whether the user has a team or not")]

    team_info: Annotated[
        ParticipantTeamInfo | None,
        Field(description="Information about the user's team, if applicable"),
    ] = None

    referral_source: Annotated[
        str, Field(description="How the user heard about the hackathon")
    ]

    expectations: Annotated[
        str | None, Field(description="What the user expects from the hackathon")
    ] = None

    comments: Annotated[
        str | None, Field(description="Additional comments from the user")
    ] = None

    gdpr_consent: Annotated[
        Literal[True], Field(description="Whether the user consents to GDPR terms")
    ]
